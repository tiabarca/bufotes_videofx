"""
Movimientos "en reposo" de las ranas: además de respirar, de vez en cuando
cambian de postura, se ladean, se estiran para mirar alrededor o dan un
saltito a otro sitio de su nenúfar (y más tarde vuelven).

Todo se planifica antes de renderizar, a partir de los estados de boca:
cada rana solo se mueve cuando ELLA está callada (silencios suficientemente
largos para que el gesto empiece y acabe sin que hable), así que nunca salta
a media frase. Mientras la otra habla es justo cuando más se mueve, como
quien escucha.

Antes de un evento que va a por una rana en concreto (la lengua contra el
gusano o el mosquito, el pedo...) esa rana vuelve a su sitio, para que la
lengua y el humo salgan de donde toca.

planificar() devuelve, por fotograma:
    dx       desplazamiento horizontal en píxeles respecto a su sitio
    alto     altura del salto en píxeles (0 en el suelo)
    postura  0 sentada · 1 agachada · 2 en el aire · 3 erguida (ver sprite_rana)
    ladeo    inclinación en grados (-3, 0, 3)
    mira     -1/0/1 mirada propia del gesto, o SIN_MIRADA si no impone ninguna
"""

import math
import random

import numpy as np

SIN_MIRADA = 9

DUR_SALTO = 0.8
DUR_RECOLOCA = 0.55
DUR_ESTIRA = 1.8
DUR_MIRA = 2.0
INICIO_SILENCIO = 0.3   # s de silencio antes de empezar un gesto
FIN_SILENCIO = 0.2      # s de silencio que deben quedar al acabarlo
ANTES_EVENTO = 1.0      # s antes de un evento que la afecta, ya en su sitio


def _tramos(mascara):
    """Lista de (inicio, fin) de los tramos True de una máscara booleana."""
    m = np.concatenate(([False], mascara, [False])).astype(np.int8)
    cambios = np.flatnonzero(np.diff(m))
    return list(zip(cambios[0::2], cambios[1::2]))


def _suave(u):
    return u * u * (3 - 2 * u)


def planificar(boca, fps, W, H, semilla, bloqueos=(), hacia_fuera=-1, escala=1.0, inquietud=1.0):
    """
    boca: estados de boca de la rana (0 = callada) por fotograma.
    bloqueos: lista de (inicio, fin) en fotogramas en los que la rana debe
    estar en su sitio y quieta (eventos que la afectan).
    hacia_fuera: -1 si el borde de pantalla más cercano queda a la izquierda.
    inquietud: 0 = solo respira (como antes); 1 = normal; 2 = el doble de gestos.
    """
    n = len(boca)
    rng = random.Random(semilla)
    dx = np.zeros(n, np.float32)
    alto = np.zeros(n, np.float32)
    postura = np.zeros(n, np.int8)
    ladeo = np.zeros(n, np.int8)
    mira = np.full(n, SIN_MIRADA, np.int8)
    if inquietud <= 0 or n == 0:
        return dx, alto, postura, ladeo, mira

    # dónde puede ponerse dentro del nenúfar (fracción del ancho): más
    # margen hacia fuera que hacia el micro y la otra rana
    lejos, cerca = 0.035 * W, 0.012 * W
    h_salto = 0.045 * H * escala

    libre = np.asarray(boca) == 0
    bloq = np.zeros(n, bool)
    lista_bloqueos = []
    for a, b in sorted(bloqueos):
        a2 = max(0, a - int(ANTES_EVENTO * fps))
        bloq[a2:min(n, b)] = True
        lista_bloqueos.append(a2)
    ventanas = _tramos(libre & ~bloq)

    pos, lad = 0.0, 0                 # estado que se mantiene entre gestos
    t_libre = int(2 * fps)            # nada en los dos primeros segundos
    acciones = []                     # (inicio, duración, tipo, pos0, pos1, lad1, extra)

    def hueco():
        return int(rng.uniform(3.0, 9.0) * fps / inquietud)

    def volver_antes(limite):
        """Si al llegar a 'limite' no está en su sitio, vuelve de un salto justo antes."""
        nonlocal pos, lad, t_libre
        if pos == 0 and lad == 0:
            return
        d = int(DUR_SALTO * fps)
        ini = max(t_libre, limite - d)
        acciones.append((ini, d, "salto", pos, 0.0, 0, None))
        pos, lad = 0.0, 0
        t_libre = ini + d

    ib = 0
    for va, vb in ventanas:
        # bloqueos que empiezan antes de esta ventana: llegar a ellos en casa
        while ib < len(lista_bloqueos) and lista_bloqueos[ib] <= va:
            volver_antes(lista_bloqueos[ib])
            ib += 1
        a = max(va + int(INICIO_SILENCIO * fps), t_libre)
        fin = vb - int(FIN_SILENCIO * fps)
        prox_bloqueo = lista_bloqueos[ib] if ib < len(lista_bloqueos) else n + 10 ** 9
        while True:
            disp = (fin - a) / fps
            if disp < DUR_RECOLOCA:
                break
            fuera_de_casa = pos != 0 or lad != 0
            cerca_evento = (prox_bloqueo - a) / fps < 8   # pronto le toca: no se aleja
            if fuera_de_casa and cerca_evento and disp >= DUR_SALTO:
                tipo = "salto"
                destino = 0.0
            else:
                opciones = [("mira", 3)] if cerca_evento else [("recoloca", 3), ("mira", 3)]
                if disp >= DUR_SALTO and not cerca_evento:
                    opciones.append(("salto", 4))
                if disp >= DUR_ESTIRA:
                    opciones.append(("estira", 2))
                total = sum(p for _, p in opciones)
                x = rng.uniform(0, total)
                for tipo, p in opciones:
                    x -= p
                    if x <= 0:
                        break
                destino = pos
                if tipo == "salto":
                    if pos != 0 and rng.random() < 0.45:
                        destino = 0.0
                    else:
                        for _ in range(10):
                            destino = rng.uniform(-cerca, lejos) * hacia_fuera
                            if abs(destino - pos) > 0.01 * W:
                                break
            if tipo == "salto":
                d = int(DUR_SALTO * fps)
                acciones.append((a, d, "salto", pos, destino, 0, None))
                pos, lad = destino, 0
            elif tipo == "recoloca":
                d = int(DUR_RECOLOCA * fps)
                nuevo = rng.choice([v for v in (-3, 0, 3) if v != lad])
                acciones.append((a, d, "recoloca", pos, pos, nuevo, None))
                lad = nuevo
            elif tipo == "estira":
                d = int(DUR_ESTIRA * fps)
                acciones.append((a, d, "estira", pos, pos, lad, rng.choice((-1, 1))))
            else:
                d = int(DUR_MIRA * fps)
                secuencia = rng.choice(((-1, 1), (1, -1), (-1, 0, 1), (1, 0, -1), (0, -1), (0, 1)))
                acciones.append((a, d, "mira", pos, pos, lad, secuencia))
            t_libre = a + d
            a = t_libre + hueco()
            if a >= fin:
                break
    while ib < len(lista_bloqueos):
        volver_antes(lista_bloqueos[ib])
        ib += 1

    # --- volcar las acciones a los arrays (el estado se mantiene hasta la siguiente)
    acciones.sort(key=lambda x: x[0])
    pos_act, lad_act, t = 0.0, 0, 0
    for ini, d, tipo, p0, p1, l1, extra in acciones:
        ini = max(ini, t)
        if ini >= n:
            break
        dx[t:ini] = pos_act
        ladeo[t:ini] = lad_act
        for j in range(d):
            i = ini + j
            if i >= n:
                break
            u = j / max(1, d - 1)
            if tipo == "salto":
                ladeo[i] = 0
                if u < 0.22:                       # coge impulso
                    postura[i], dx[i] = 1, p0
                elif u < 0.78:                     # en el aire
                    v = (u - 0.22) / 0.56
                    postura[i] = 2
                    dx[i] = p0 + (p1 - p0) * _suave(v)
                    alto[i] = math.sin(math.pi * v) * h_salto
                else:                              # aterriza
                    postura[i], dx[i] = 1, p1
                if abs(p1 - p0) > 1:
                    mira[i] = 1 if p1 > p0 else -1
            elif tipo == "recoloca":
                dx[i] = p0
                postura[i] = 1 if 0.15 < u < 0.7 else 0
                ladeo[i] = lad_act if u < 0.5 else l1
            elif tipo == "estira":
                dx[i], ladeo[i] = p0, lad_act
                postura[i] = 1 if u < 0.08 else (3 if u < 0.92 else 0)
                if 0.15 < u < 0.85:
                    mira[i] = extra if u < 0.5 else -extra
            else:  # mira
                dx[i], ladeo[i] = p0, lad_act
                if 0.05 < u < 0.95:
                    mira[i] = extra[min(len(extra) - 1, int((u - 0.05) / 0.9 * len(extra)))]
        pos_act, lad_act = p1, l1
        t = min(n, ini + d)
    dx[t:] = pos_act
    ladeo[t:] = lad_act
    return dx, alto, postura, ladeo, mira
