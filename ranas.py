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

from audio import (FFMPEG, SR, cargar_audio, centroide_por_fotograma, diagnostico, estados_boca,
                    nivel_por_fotograma, tasa_cruces_por_fotograma)
from escena import (X_RANAS, Nubes, dibujar_canas, dibujar_microfonos, dibujar_molino, dibujar_nenufares,
                     dibujar_reflejos, fondo_mallorquin, generar_canas, generar_microfonos, generar_molino,
                     generar_nenufares, generar_reflejos)
from eventos import SOLAPABLES, TIPOS, programar_eventos
import eventos_extra  # noqa: F401  (registra los eventos nuevos en TIPOS)
from midi import cargar_mapa, eventos_midi
from overlay import cargar_logo, cargar_portada, con_alpha, dibujar_titulo, factor_portada, factor_titulo
from personajes import cargar_sprites

# la consola de Windows usa cp1252 y revienta con caracteres como → o ≈
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


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
    ap.add_argument("--midi", help="Pista MIDI (.mid): cada nota lanza un evento en su instante exacto, "
                                   "además de los aleatorios")
    ap.add_argument("--midi-mapa", metavar="INI", help="Mapa nota -> evento (por defecto, midi_mapa.ini)")
    ap.add_argument("--midi-desfase", type=float, default=0.0, metavar="SEG",
                    help="Segundos a sumar a las notas MIDI (negativo = antes)")
    ap.add_argument("--midi-canal", type=int, choices=range(1, 17), metavar="1-16",
                    help="Usar solo las notas de este canal MIDI")
    ap.add_argument("--semilla", type=int, help="Semilla para repetir el mismo orden de eventos")
    ap.add_argument("--titulo", help='Título de entrada (p. ej. "Bufotes Episodio 94"), aparece tras la portada')
    ap.add_argument("--titulo-duracion", type=float, default=10.0, metavar="SEG",
                    help="Cuánto dura en pantalla el título de entrada")
    ap.add_argument("--sin-logo", action="store_true", help="No poner el logo en la esquina")
    ap.add_argument("--sin-portada", action="store_true",
                    help="No abrir con la portada (media/portada.jpg) solapada sobre el arranque")
    ap.add_argument("--portada-duracion", type=float, default=5.0, metavar="SEG",
                    help="Cuánto tarda la portada en desvanecerse sobre la escena, al principio")
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
    if args.mezcla:
        # el vídeo dura lo que dure el audio final, no lo que duren las pistas de referencia
        n_mezcla = int(len(cargar_audio(args.mezcla, args.duracion)) / SR * fps)
        if n_mezcla < n:
            print(f"  Las pistas A/B duran {n / fps / 60:.1f} min y la mezcla {n_mezcla / fps / 60:.1f} min: "
                  f"se usa la duración de la mezcla")
            n = n_mezcla
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
    agenda = agenda + agenda2
    if args.midi:
        agenda_midi, usados = eventos_midi(args.midi, fps, W, H, TIPOS, cargar_mapa(args.midi_mapa),
                                           args.midi_desfase, args.midi_canal, n, semilla)
        agenda = agenda + agenda_midi
        if usados:
            notas = sorted(usados.items(), key=lambda kv: kv[0])
            print(f"  MIDI: {len(agenda_midi)} eventos -> " + ", ".join(f"{k}:{v}" for k, v in notas))
    agenda.sort(key=lambda x: x[0])  # para que "el más reciente" tenga sentido al mirar varios a la vez

    # eventos activos en cada fotograma: pueden coincidir varios (agenda normal,
    # el solapable y los del MIDI), así que cada fotograma guarda una lista de índices
    activo_en = [[] for _ in range(n)]
    for idx, (ini, ev) in enumerate(agenda):
        for i in range(ini, min(n, ini + ev.duracion)):
            activo_en[i].append(idx)

    if agenda:
        resumen = {}
        for _, ev in agenda:
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
        viento = {}
        for ev, t_ev in activos:
            viento_fn = getattr(ev, "viento", None)
            if viento_fn is not None:
                for lado, px in viento_fn(t_ev).items():
                    viento[lado] = viento.get(lado, 0.0) + px
        dibujar_canas(draw, canas, t_seg, H, viento)
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
    audio_in = ["-i", args.mezcla] if args.mezcla else ["-i", args.a, "-i", args.b]
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
    log_ffmpeg = os.path.splitext(args.salida)[0] + "_ffmpeg.log"
    flog = open(log_ffmpeg, "w", encoding="utf-8", errors="replace")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=flog)
    periodo_resp = [3.6 * fps, 4.1 * fps]
    margen_mirada = 0.06 * W
    try:
        for i in range(n):
            activos = [(agenda[k][1], i - agenda[k][0]) for k in activo_en[i]]

            x_ev = None
            boca_forzada = None
            for ev, t_ev in reversed(activos):  # el que ha empezado más recientemente manda
                if x_ev is None:
                    x_ev = ev.x_interes(t_ev)
                if boca_forzada is None:
                    forzar = getattr(ev, "boca_forzada", None)
                    if forzar is not None:
                        boca_forzada = forzar(t_ev)

            # eventos que afectan a una rana en concreto (p. ej. el pedo: bote y ojos cerrados)
            efectos = {}
            for ev, t_ev in activos:
                afecta = getattr(ev, "afecta_rana", None)
                if afecta is not None:
                    for rr, ef in afecta(t_ev).items():
                        efectos.setdefault(rr, []).append(ef)

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
                ojos = not parpadeo[r][i]
                for ef in efectos.get(r, ()):
                    bote = max(bote, ef.get("bote", 0))
                    ojos = ojos and ef.get("ojos", True)
                estado.append((b, ojos, mira, bote, resp))
            try:
                proc.stdin.write(componer(i, tuple(estado), activos))
            except (BrokenPipeError, OSError):
                print(f"\nffmpeg se ha cerrado en el fotograma {i} ({i / fps / 60:.1f} min de vídeo).")
                break
            if i % (fps * 60) == 0 and i:
                v = i / (time.time() - t0)
                print(f"  {i / fps / 60:.0f} min · {v:.0f} fps · faltan ~{(n - i) / v / 60:.1f} min")
    finally:
        try:
            proc.stdin.close()
        except OSError:
            pass
        proc.wait()
        flog.close()

    if proc.returncode != 0:
        with open(log_ffmpeg, encoding="utf-8", errors="replace") as f:
            ultimas = f.read().strip().splitlines()[-15:]
        print("Últimas líneas de ffmpeg:\n  " + "\n  ".join(ultimas or ["(ffmpeg no dijo nada)"]))
        sys.exit(f"ffmpeg ha fallado (código {proc.returncode}). Log completo: {log_ffmpeg}")
    os.remove(log_ffmpeg)
    print(f"Listo: {args.salida} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
