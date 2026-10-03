#!/usr/bin/env python3
"""
ranas.py — Convierte un podcast de 2 pistas en un vídeo de dos ranas hablando
en un estanque de la Serra de Tramuntana, con tractores, cerdos, pájaros y
gusanos que pasan de vez en cuando.

Requisitos: Python 3.9+, numpy, Pillow y ffmpeg (en el PATH o junto al script).
    pip install -r requirements.txt

Ejemplos:
    python ranas.py --a A.mp3 --b B.mp3 --analizar
    python ranas.py --a A.mp3 --b B.mp3 --mezcla master.mp3 --umbral -27 -o episodio.mp4
    python ranas.py --a A.mp3 --b B.mp3 --duracion 60 -o prueba.mp4
"""

import argparse
import math
import os
import random
import shutil
import subprocess
import sys
import time
from collections import OrderedDict

import numpy as np
from PIL import Image, ImageDraw

from audio import (FFMPEG, cargar_audio, centroide_por_fotograma, diagnostico, estados_boca,
                    nivel_por_fotograma, tasa_cruces_por_fotograma)
from escena import (X_RANAS, Nubes, dibujar_canas, dibujar_microfonos, dibujar_molino, dibujar_nenufares,
                     dibujar_reflejos, fondo_mallorquin, generar_canas, generar_microfonos, generar_molino,
                     generar_nenufares, generar_reflejos)
from eventos import SOLAPABLES, TIPOS, programar_eventos
from overlay import cargar_logo, cargar_portada, con_alpha, dibujar_titulo, factor_portada, factor_titulo
from personajes import cargar_sprites


class LRU(OrderedDict):
    def __init__(self, maximo):
        super().__init__()
        self.maximo = maximo

    def get(self, k):
        if k in self:
            self.move_to_end(k)
            return self[k]
        return None

    def put(self, k, v):
        self[k] = v
        if len(self) > self.maximo:
            self.popitem(last=False)


# rebote vertical según el estado de boca (ver GEOM_BOCA en personajes.py);
# el grito (6) salta mucho más, para que se note que la rana está exaltada
BOTE_POR_BOCA = {0: 0, 1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 6}


def horario_parpadeos(n, fps, semilla):
    rng = random.Random(semilla)
    cerrado = np.zeros(n, dtype=bool)
    i = int(rng.uniform(1, 4) * fps)
    dur = max(2, int(0.12 * fps))
    while i < n:
        cerrado[i:i + dur] = True
        if rng.random() < 0.15:  # parpadeo doble de vez en cuando
            cerrado[i + dur * 2:i + dur * 3] = True
        i += int(rng.uniform(2.5, 6.0) * fps)
    return cerrado


def main():
    ap = argparse.ArgumentParser(description="Podcast de 2 pistas → vídeo de ranas en Mallorca")
    ap.add_argument("--a", required=True, help="Pista del interlocutor A (rana izquierda)")
    ap.add_argument("--b", required=True, help="Pista del interlocutor B (rana derecha)")
    ap.add_argument("--mezcla", help="Audio final del vídeo (si no, se mezclan A y B)")
    ap.add_argument("-o", "--salida", default="episodio.mp4")
    ap.add_argument("--assets", help="Carpeta con fondo.png y sprites propios de las ranas")
    ap.add_argument("--ancho", type=int, default=1280)
    ap.add_argument("--alto", type=int, default=720)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--duracion", type=float, help="Renderizar solo los primeros N segundos")
    ap.add_argument("--umbral", type=float, nargs="+", metavar="dBFS",
                    help="Nivel mínimo para que la boca se active (p. ej. -35). Uno para ambas o dos: A B")
    ap.add_argument("--analizar", action="store_true",
                    help="Solo mostrar los niveles de cada pista y el umbral sugerido")
    ap.add_argument("--sensibilidad", type=float, default=0.0,
                    help="dB extra de sensibilidad de la boca (positivo = abre más fácil)")
    ap.add_argument("--antisangrado", type=float, default=None,
                    help="Atenuación del sangrado entre micros en dB (por defecto se estima sola)")
    ap.add_argument("--accesorios", nargs=2, default=["sombrero", "gafas"], metavar=("A", "B"),
                    choices=["sombrero", "gafas", "nada"], help="Accesorio de cada rana")
    ap.add_argument("--tamano-ranas", type=float, default=0.8, metavar="FACTOR",
                    help="Tamaño de las ranas (1.0 = el original, más grandes)")
    ap.add_argument("--eventos", nargs="*", default=list(TIPOS), choices=list(TIPOS),
                    help="Qué puede pasar por la escena (por defecto todos). Sin valores: ninguno")
    ap.add_argument("--eventos-cada", type=float, default=25.0, metavar="SEG",
                    help="Segundos de media entre eventos (0 = desactivar)")
    ap.add_argument("--semilla", type=int, help="Semilla para repetir el mismo orden de eventos")
    ap.add_argument("--titulo", help='Título de entrada (p. ej. "Bufotes Episodio 94"), aparece tras la portada')
    ap.add_argument("--titulo-duracion", type=float, default=10.0, metavar="SEG",
                    help="Cuánto dura en pantalla el título de entrada")
    ap.add_argument("--sin-logo", action="store_true", help="No poner el logo en la esquina")
    ap.add_argument("--sin-portada", action="store_true",
                    help="No abrir con la portada (media/portada.jpg) solapada sobre el arranque")
    ap.add_argument("--portada-duracion", type=float, default=5.0, metavar="SEG",
                    help="Cuánto tarda la portada en desvanecerse sobre la escena, al principio")
    ap.add_argument("--sin-recorte", action="store_true",
                    help="No recortar el silencio inicial antes de la primera palabra "
                         "(con --mezcla nunca se recorta, por si lleva música de entrada)")
    ap.add_argument("--crf", type=int, default=23, help="Calidad x264 (menor = mejor, más pesado)")
    ap.add_argument("--preset", default="veryfast", help="Preset x264")
    args = ap.parse_args()

    if not (os.path.isfile(FFMPEG) or shutil.which(FFMPEG)):
        sys.exit("No encuentro ffmpeg. Instálalo o copia ffmpeg.exe junto a ranas.py.")

    W, H, fps = args.ancho, args.alto, args.fps
    semilla = args.semilla if args.semilla is not None else random.randrange(10000)
    t0 = time.time()

    # --- audio -> estados de boca
    print("Analizando audio…")
    aa = cargar_audio(args.a, args.duracion)
    ab = cargar_audio(args.b, args.duracion)
    n_muestras = max(len(aa), len(ab))
    aa = np.pad(aa, (0, n_muestras - len(aa)))
    ab = np.pad(ab, (0, n_muestras - len(ab)))
    da, db = nivel_por_fotograma(aa, fps), nivel_por_fotograma(ab, fps)
    n = min(len(da), len(db))
    da, db = da[:n], db[:n]

    if args.analizar:
        diagnostico("A", da, db)
        diagnostico("B", db, da)
        return

    za, zb = tasa_cruces_por_fotograma(aa, fps)[:n], tasa_cruces_por_fotograma(ab, fps)[:n]
    ca, cb = centroide_por_fotograma(aa, fps)[:n], centroide_por_fotograma(ab, fps)[:n]
    umb = (args.umbral or [None]) * 2 if not args.umbral or len(args.umbral) == 1 else args.umbral[:2]
    boca = [estados_boca(da, db, za, ca, args.sensibilidad, args.antisangrado, umb[0]),
            estados_boca(db, da, zb, cb, args.sensibilidad, args.antisangrado, umb[1])]

    # recorta el silencio inicial (antes de que nadie hable) para que la
    # conversación arranque justo al acabar la portada, no después de un hueco.
    # Solo si no hay --mezcla: esa pista puede llevar música de entrada que no
    # sale en los micros sueltos de A/B, y no hay forma de distinguirla desde
    # aquí del silencio real, así que un máster ya montado se deja intacto.
    recorte_seg = 0.0
    if not args.sin_recorte and not args.mezcla:
        hablando = (boca[0] > 0) | (boca[1] > 0)
        primero = int(np.argmax(hablando)) if hablando.any() else 0
        recorte = max(0, primero - int(0.3 * fps))
        if recorte:
            boca = [b[recorte:] for b in boca]
            n -= recorte
            recorte_seg = recorte / fps
            print(f"  Recortados {recorte_seg:.1f}s de silencio inicial")
    parpadeo = [horario_parpadeos(n, fps, semilla + 1), horario_parpadeos(n, fps, semilla + 2)]
    print(f"  {n} fotogramas ({n / fps / 60:.1f} min). "
          f"A habla {np.mean(boca[0] > 0) * 100:.0f}% · B habla {np.mean(boca[1] > 0) * 100:.0f}%")

    # --- escena, ranas y eventos
    escala = H / 720
    if args.assets and os.path.exists(os.path.join(args.assets, "fondo.png")):
        fondo = Image.open(os.path.join(args.assets, "fondo.png")).convert("RGB").resize((W, H))
    else:
        fondo = fondo_mallorquin(W, H)
    accs = [None if a == "nada" else a for a in args.accesorios]
    sprites = cargar_sprites(args.assets, [(95, 170, 80), (150, 185, 60)], escala * args.tamano_ranas, accs)
    anclas = [(int(W * X_RANAS[0]), int(H * 0.86)), (int(W * X_RANAS[1]), int(H * 0.86))]

    nubes = Nubes(n, fps, W, H, semilla)
    canas = generar_canas(W, H, semilla)
    reflejos = generar_reflejos(W, H, semilla)
    nenufares = generar_nenufares(W, H, semilla)
    micros = generar_microfonos(W, H, H * 0.875, escala)
    molino = generar_molino(W, H)
    logo = None if args.sin_logo else cargar_logo(H)
    margen_logo = int(0.03 * H)
    portada = None if args.sin_portada else cargar_portada(W, H)
    inicio_titulo = args.portada_duracion if portada is not None else 0.0
    titulo = dibujar_titulo(args.titulo, W, escala) if args.titulo else None
    y_titulo = int(0.1 * H)

    tipos_normales = [t for t in args.eventos if t not in SOLAPABLES]
    tipos_solapables = [t for t in args.eventos if t in SOLAPABLES]
    agenda = programar_eventos(n, fps, W, H, tipos_normales, args.eventos_cada, semilla, args.assets)
    # los solapables son un chiste puntual, no un relleno constante: mucho más espaciados
    agenda2 = programar_eventos(n, fps, W, H, tipos_solapables, args.eventos_cada * 5, semilla + 5000, args.assets)

    def _activos(agenda_):
        activo_ = [None] * n
        for idx, (ini, ev) in enumerate(agenda_):
            for i in range(ini, min(n, ini + ev.duracion)):
                activo_[i] = idx
        return activo_

    activo = _activos(agenda)
    activo2 = _activos(agenda2)
    if agenda or agenda2:
        resumen = {}
        for _, ev in agenda + agenda2:
            nombre = type(ev).__name__.lower()
            resumen[nombre] = resumen.get(nombre, 0) + 1
        print(f"  Eventos: {', '.join(f'{v} {k}' for k, v in resumen.items())} (semilla {semilla})")

    # sprites de rana ya transformados (respiración); el fondo entero no se
    # puede cachear por estado porque nubes/cañas/reflejos cambian en cada fotograma
    cache_rana = LRU(400)

    def sprite_rana(r, b, ojos, mira, resp):
        clave = (r, b, ojos, mira, resp)
        spr = cache_rana.get(clave)
        if spr is None:
            spr = sprites[r][(b, ojos, mira)]
            if resp:  # respiración: estirar un poco en vertical
                spr = spr.resize((spr.width, int(spr.height * (1 + 0.015 * resp))), Image.BILINEAR)
            cache_rana.put(clave, spr)
        return spr

    def pegar_ranas(img, estado):
        for r in (0, 1):
            b, ojos, mira, bote, resp = estado[r]
            spr = sprite_rana(r, b, ojos, mira, resp)
            x = anclas[r][0] - spr.width // 2
            y = anclas[r][1] - spr.height - int(bote * 4 * escala)
            img.paste(spr, (x, y), spr)

    def componer(i, estado, activos):
        img = fondo.copy()
        draw = ImageDraw.Draw(img)
        for spr, x, y in nubes.sprites(i):
            img.paste(spr, (x, y), spr)
        t_seg = i / fps
        dibujar_molino(draw, molino, t_seg)
        dibujar_canas(draw, canas, t_seg, H)
        dibujar_reflejos(draw, reflejos, t_seg, W)
        dibujar_nenufares(img, nenufares)

        for ev, t_ev in activos:
            if ev.capa == "fondo":
                for im, x, y in ev.sprites(t_ev):
                    img.paste(im, (x, y), im)
        pegar_ranas(img, estado)
        dibujar_microfonos(img, micros)
        for ev, t_ev in activos:
            if ev.capa == "frente":
                for im, x, y in ev.sprites(t_ev):
                    img.paste(im, (x, y), im)
        if logo is not None:
            img.paste(logo, (margen_logo, margen_logo), logo)
        if titulo is not None:
            fa = factor_titulo(t_seg - inicio_titulo, args.titulo_duracion)
            if fa > 0.003:
                capa = con_alpha(titulo, fa)
                img.paste(capa, (0, y_titulo), capa)
        if portada is not None:
            fp = factor_portada(t_seg, args.portada_duracion)
            if fp > 0.003:
                capa = con_alpha(portada, fp)
                img.paste(capa, (0, 0), capa)
        return img.tobytes()

    # --- ffmpeg: fotogramas crudos por stdin + audio
    # el mismo recorte de silencio inicial que se aplicó a boca/n, para que
    # el audio real arranque exactamente donde arranca el vídeo
    ss = ["-ss", f"{recorte_seg:.3f}"] if recorte_seg else []
    audio_in = ss + ["-i", args.mezcla] if args.mezcla else ss + ["-i", args.a] + ss + ["-i", args.b]
    filtro = [] if args.mezcla else ["-filter_complex",
                                     "[1:a][2:a]amix=inputs=2:duration=longest:normalize=0[aout]"]
    mapa_audio = ["-map", "1:a"] if args.mezcla else ["-map", "[aout]"]
    cmd = ([FFMPEG, "-v", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-"]
           + audio_in + filtro
           + ["-map", "0:v"] + mapa_audio
           + ["-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
              "-tune", "animation", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart"]
           + (["-t", str(args.duracion)] if args.duracion else [])
           + [args.salida])

    print("Renderizando…")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    periodo_resp = [3.6 * fps, 4.1 * fps]
    margen_mirada = 0.06 * W
    try:
        for i in range(n):
            activos = []
            for agenda_, activo_ in ((agenda, activo), (agenda2, activo2)):
                idx = activo_[i]
                if idx is not None:
                    ini, ev = agenda_[idx]
                    activos.append((ev, i - ini))

            x_ev = None
            boca_forzada = None
            for ev, t_ev in activos:  # la agenda principal manda sobre la solapable si ambas opinan
                if x_ev is None:
                    x_ev = ev.x_interes(t_ev)
                if boca_forzada is None:
                    forzar = getattr(ev, "boca_forzada", None)
                    if forzar is not None:
                        boca_forzada = forzar(t_ev)

            estado = []
            for r in (0, 1):
                b = int(boca[r][i])
                if boca_forzada is not None and boca_forzada[0] == r:
                    b = boca_forzada[1]
                bote = BOTE_POR_BOCA[b]
                resp = round((math.sin(2 * math.pi * i / periodo_resp[r]) + 1) * 1.5)  # 0..3
                if x_ev is not None and -0.05 * W < x_ev < 1.05 * W:
                    dx = x_ev - anclas[r][0]  # las dos miran lo que pasa
                    mira = 0 if abs(dx) < margen_mirada else (1 if dx > 0 else -1)
                else:
                    mira = 1 if r == 0 else -1  # se miran entre ellas
                estado.append((b, not parpadeo[r][i], mira, bote, resp))
            try:
                proc.stdin.write(componer(i, tuple(estado), activos))
            except BrokenPipeError:
                break  # ffmpeg ha muerto a media; el returncode/stderr de abajo dirá por qué
            if i % (fps * 60) == 0 and i:
                v = i / (time.time() - t0)
                print(f"  {i / fps / 60:.0f} min · {v:.0f} fps · faltan ~{(n - i) / v / 60:.1f} min")
    finally:
        try:
            proc.stdin.close()
        except BrokenPipeError:
            pass
        proc.wait()

    if proc.returncode != 0:
        sys.exit("ffmpeg devolvió un error (código "
                  f"{proc.returncode}); mira el mensaje de ffmpeg más arriba.")
    print(f"Listo: {args.salida} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
