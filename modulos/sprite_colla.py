"""
Dibujos de la colla de xeremiers (evento "xeremiers"), con el mismo estilo que
el músico del evento "cabra" (modulos/sprite_payes_tambor.py):

    xeremier      pagès tocando la xeremia: sac de tela a cuadros bajo el brazo,
                  bordons por encima del hombro con borles rojas, soplador a la
                  boca y grall con las dos manos. Lienzo 120 x 130.
    fabioler      flabiol y tamborí, como el de la cabra pero caminando y con
                  otra armilla. Lienzo 100 x 130.
    payes_baila   ballador de ball de bot: mocador al cap, camisa, armilla, faixa,
                  calçons de bufa; salta con los brazos en alto y castanyoles.
                  Lienzo 90 x 135.
    payesa_baila  balladora: rebosillo blanco, cosset negro con cordones, mànigues
                  oscuras, faldilla de vuelo con davantal; castanyoles. Lienzo 90 x 135.

Los cuatro miran a la derecha y tienen los pies en el borde inferior.
paso (músicos) y fase (balladors) van de 0 a 3, igual que en eventos.py.
"""

import math

from . import sprite_payes_tambor as _pt
from .sprite_payes_tambor import (BARRET, BARRET_LUZ, BIGOTE, BOTON, CALCES, CALCONS, CALCONS_LUZ, CAMISA, CINTA,
                                  ESPARDENYA, LINEA, MADERA, MADERA_OSC, MEJILLA, PIEL, PIEL_SOMBRA, _curva, _Lienzo)

BOSSA = (48, 92, 62)          # tela del sac de la xeremia
BOSSA_RAYA = (176, 44, 44)
BORLA = (200, 40, 50)
ARMILLA_XEREMIER = (92, 50, 36)
FAIXA_XEREMIER = (40, 70, 140)
ARMILLA_BALL = (30, 30, 34)
FAIXA_BALL = (196, 150, 40)
MOCADOR = (186, 36, 40)
CASTANYOLA = (110, 64, 34)
REBOSILLO = (250, 250, 246)
REBOSILLO_SOMBRA = (220, 220, 214)
COSSET = (26, 24, 30)
CORDON = (226, 190, 90)
MANIGA = (44, 40, 52)
FALDILLA = (150, 34, 48)
FALDILLA_FLOR = (238, 200, 90)
DAVANTAL = (40, 46, 70)
DAVANTAL_VORA = (210, 180, 120)
SABATA = (30, 26, 26)


# ----------------------------------------------------------------------------
# Piezas comunes
# ----------------------------------------------------------------------------

def _piernas_payes(lz, xs, cintura, suelo, abre=(0, 0)):
    """Calçons de bufa, calces blancas con cintas y espardenyes. abre: desplazamiento de cada pie."""
    pies = []
    for (x, a) in zip(xs, abre):
        pie = x + a
        lz.poli([(x - 5, cintura + 18), (x + 5, cintura + 18), (pie + 4, suelo - 6), (pie - 4, suelo - 6)], CALCES)
        for f in (0.35, 0.65):
            yy = cintura + 18 + (suelo - 6 - cintura - 18) * f
            xm = x + (pie - x) * f
            lz.linea([(xm - 4.5, yy), (xm + 4.5, yy + 2)], CINTA, 0.8)
        lz.elipse(pie + 1, suelo - 3, 7, 3.5, ESPARDENYA)
        lz.linea([(pie - 4, suelo - 5), (pie + 3, suelo - 7)], CINTA, 1.0)
        pies.append(pie)
    x0, x1 = xs[0], xs[-1]
    lz.poli([(x0 - 9, cintura), (x1 + 9, cintura), (x1 + 11, cintura + 13), (x1 + 6, cintura + 21),
             (x1 - 6, cintura + 19), ((x0 + x1) / 2, cintura + 11), (x0 + 6, cintura + 19), (x0 - 6, cintura + 21),
             (x0 - 11, cintura + 13)], CALCONS)
    lz.linea(_curva((x0, cintura + 4), (x0 - 2, cintura + 12), (x0, cintura + 18), 6), CALCONS_LUZ, 1.6)
    lz.linea(_curva((x1, cintura + 4), (x1 + 2, cintura + 12), (x1, cintura + 18), 6), CALCONS_LUZ, 1.6)
    return pies


def _torso_payes(lz, cx, arriba, cintura, armilla, faixa, ancho=22):
    """Camisa blanca, armilla con botones y faixa."""
    luz = tuple(min(255, c + 24) for c in armilla)
    lz.poli([(cx - ancho, arriba), (cx + ancho, arriba), (cx + ancho + 2, cintura), (cx - ancho - 2, cintura)], CAMISA)
    lz.poli([(cx - ancho + 2, arriba + 2), (cx - 5, arriba + 2), (cx - 4, cintura), (cx - ancho, cintura)], armilla)
    lz.poli([(cx + 5, arriba + 2), (cx + ancho - 2, arriba + 2), (cx + ancho, cintura), (cx + 4, cintura)], armilla)
    lz.linea([(cx - ancho + 4, arriba + 6), (cx - ancho + 6, cintura - 4)], luz, 1.4)
    n = max(2, int((cintura - arriba) / 7))
    for i in range(n):
        y = arriba + 6 + i * 6.5
        lz.elipse(cx - 7.5, y, 1.1, 1.1, BOTON, ancho=0.6)
        lz.elipse(cx + 7.5, y, 1.1, 1.1, BOTON, ancho=0.6)
    lz.poli([(cx - ancho - 2, cintura - 2), (cx + ancho + 2, cintura - 2), (cx + ancho + 2, cintura + 5),
             (cx - ancho - 2, cintura + 5)], faixa)
    lz.poli([(cx + ancho - 8, cintura + 3), (cx + ancho - 2, cintura + 3), (cx + ancho, cintura + 14),
             (cx + ancho - 6, cintura + 13)], faixa)


def _cara(lz, cx, cy, ojos="abiertos", bigote=True, boca="sonrisa", mofletes=False, mujer=False):
    lz.elipse(cx, cy, 12, 13, PIEL)
    if not mujer:
        lz.elipse(cx - 12.5, cy + 1, 2.6, 3.6, PIEL_SOMBRA, ancho=1.0)
    r = 4.4 if mofletes else 3.2
    lz.elipse(cx - 6, cy + 6, r, r * 0.7, MEJILLA, outline=None)
    lz.elipse(cx + 7, cy + 6, r, r * 0.7, MEJILLA, outline=None)
    for x in (cx - 5, cx + 6):
        if ojos == "cerrados":
            lz.linea(_curva((x - 2.6, cy - 1), (x, cy + 1), (x + 2.6, cy - 1), 4), LINEA, 1.3)
        else:
            lz.elipse(x, cy - 1, 1.6, 2.0, LINEA, outline=None)
            lz.elipse(x + 0.5, cy - 1.7, 0.6, 0.6, (255, 255, 255), outline=None)
        if mujer:  # pestañas
            lz.linea([(x + 1.6, cy - 2.6), (x + 3.2, cy - 3.8)], LINEA, 0.8)
    lz.elipse(cx + 1, cy + 3, 2.6 if mujer else 3.2, 3.2 if mujer else 4.2, PIEL_SOMBRA, ancho=1.0)
    if bigote:
        lz.poli(_curva((cx - 8, cy + 9), (cx, cy + 5), (cx + 8, cy + 9), 8) +
                _curva((cx + 6, cy + 11), (cx, cy + 8.5), (cx - 6, cy + 11), 8), BIGOTE, ancho=1.0)
    if boca == "sonrisa":
        lz.linea(_curva((cx - 4, cy + 10 + (0 if mujer else 2)), (cx, cy + 13.5 + (0 if mujer else 2)),
                        (cx + 4, cy + 10 + (0 if mujer else 2)), 6), (150, 50, 60) if mujer else LINEA, 1.2)


def _barret(lz, cx, cy, inclina=-4):
    a = math.radians(inclina)
    c, s = math.cos(a), math.sin(a)

    def rb(x, y):
        return cx + x * c - y * s, cy + x * s + y * c

    lz.poli([rb(-21, 1), rb(21, 1), rb(19, 4), rb(-19, 4)], BARRET)
    lz.poli([rb(-11, 2), rb(-10, -9), rb(-4, -11), rb(4, -11), rb(10, -9), rb(11, 2)], BARRET)
    lz.poli([rb(-11, -1), rb(11, -1), rb(11, 2), rb(-11, 2)], BARRET_LUZ, outline=None)


def _brazo(lz, hombro, codo, mano, manga=CAMISA, piel=True):
    lz.tubo([hombro, codo, mano], [8.5, 7.5, 6.2], manga)
    if piel:
        lz.elipse(mano[0], mano[1], 4.0, 3.5, PIEL)


def _castanyola(lz, x, y):
    lz.elipse(x + 2, y - 3, 3.0, 2.2, CASTANYOLA, ancho=0.8)
    lz.linea([(x + 2, y - 5), (x + 2, y - 7)], BORLA, 1.0)


# ----------------------------------------------------------------------------
# Xeremier
# ----------------------------------------------------------------------------

def dibujar_xeremier(escala, paso=0, suavizado=4):
    lz = _Lienzo(escala, suavizado, 120, 130)
    cx, suelo, cintura = 46, 128, 88
    osc = [0, 7, 0, -7][paso % 4]
    _piernas_payes(lz, (cx - 9, cx + 9), cintura, suelo, (osc, -osc))
    _torso_payes(lz, cx, 50, cintura, ARMILLA_XEREMIER, FAIXA_XEREMIER)

    # brazo de atrás (su derecha): baja al grall
    _brazo(lz, (cx - 18, 54), (cx - 15, 80), (cx + 17, 86))

    # bordons: por encima del hombro, con anillas y borles rojas
    base = (cx + 22, 52)
    for (tx, ty), ancho in (((cx + 52, 8), 3.4), ((cx + 60, 18), 3.0), ((cx + 44, 4), 2.6)):
        lz.tubo([base, ((base[0] + tx) / 2, (base[1] + ty) / 2), (tx, ty)], [ancho, ancho * 0.9, ancho * 0.8], MADERA)
        for f in (0.4, 0.7):
            px, py = base[0] + (tx - base[0]) * f, base[1] + (ty - base[1]) * f
            lz.elipse(px, py, ancho * 0.8, ancho * 0.8, MADERA_OSC, ancho=0.6)
        lz.elipse(tx, ty, ancho, ancho, MADERA_OSC, ancho=0.8)
        lz.linea([(tx, ty + ancho), (tx - 2, ty + ancho + 6)], BORLA, 2.0)  # borla colgando
        lz.linea([(tx + 1, ty + ancho), (tx + 2, ty + ancho + 6)], BORLA, 2.0)

    # sac de tela a cuadros, apretado bajo el brazo
    sx, sy, rx, ry = cx + 22, 66, 17, 12
    lz.elipse(sx, sy, rx, ry, BOSSA, ancho=1.4)
    for i in range(-3, 4):  # rayas del cuadro, recortadas al óvalo
        for vertical in (True, False):
            pts = []
            for j in range(21):
                u = -1 + j / 10
                if vertical:
                    x, y = sx + i * rx / 4, sy + u * ry
                else:
                    x, y = sx + u * rx, sy + i * ry / 4
                if ((x - sx) / rx) ** 2 + ((y - sy) / ry) ** 2 < 0.86:
                    pts.append((x, y))
            if len(pts) > 1:
                lz.linea(pts, BOSSA_RAYA, 1.1)
    lz.linea(_curva((sx - rx + 4, sy - 2), (sx, sy - ry + 3), (sx + rx - 5, sy - 3), 8), (90, 140, 100), 1.2)

    # grall (puntero): del sac hacia abajo, con campana
    g0, g1 = (cx + 16, 76), (cx + 22, 112)
    lz.tubo([g0, ((g0[0] + g1[0]) / 2, (g0[1] + g1[1]) / 2), g1], [3.4, 3.6, 4.6], MADERA)
    lz.elipse(g1[0], g1[1] + 1, 3.4, 1.6, MADERA_OSC, ancho=0.8)
    for f in (0.35, 0.5, 0.65):
        lz.elipse(g0[0] + (g1[0] - g0[0]) * f, g0[1] + (g1[1] - g0[1]) * f, 0.7, 0.7, MADERA_OSC, outline=None)

    # cabeza soplando: mofletes hinchados
    hy = 32
    _cara(lz, cx, hy, ojos="cerrados", bigote=True, boca=None, mofletes=True)
    lz.tubo([(cx + 4, hy + 10), (cx + 12, hy + 18), (cx + 18, 56)], [2.4, 2.4, 2.4], MADERA)  # soplador
    _barret(lz, cx, hy - 11)

    # brazo de delante (su izquierda): aprieta el sac y toca el grall
    _brazo(lz, (cx + 18, 54), (cx + 30, 70), (cx + 20, 98))
    return lz.reducir()


# ----------------------------------------------------------------------------
# Fabioler (el mismo dibujo que el músico de la cabra, caminando)
# ----------------------------------------------------------------------------

def dibujar_fabioler(escala, paso=0, suavizado=4):
    return _pt.dibujar(escala, paso % 2, suavizado=suavizado, paso=paso, armilla=(70, 40, 70),
                       faixa=(30, 110, 80))


# ----------------------------------------------------------------------------
# Balladors
# ----------------------------------------------------------------------------

_BOTE = (0, -10, 0, -6)
_BRAZOS = (18, 30, 18, 8)
_ABRE = (5, 12, 5, 1)


def dibujar_payes_baila(escala, fase=0, suavizado=4):
    lz = _Lienzo(escala, suavizado, 90, 135)
    f = fase % 4
    b, br, ab = _BOTE[f], _BRAZOS[f], _ABRE[f]
    cx, suelo, cintura = 45, 133 + b, 92 + b
    # piernas: en el salto, una se recoge hacia atrás (punta del ball de bot)
    _piernas_payes(lz, (cx - 9, cx + 9), cintura, suelo, (-ab, ab))
    _torso_payes(lz, cx, 54 + b, cintura, ARMILLA_BALL, FAIXA_BALL, ancho=20)
    hy = 36 + b
    _cara(lz, cx, hy, ojos="abiertos", bigote=False, boca="sonrisa")
    # mocador al cap, anudado detrás
    lz.poli(_curva((cx - 13, hy - 2), (cx, hy - 22), (cx + 13, hy - 2), 10) + [(cx + 11, hy - 6), (cx - 11, hy - 6)],
            MOCADOR)
    lz.poli([(cx - 12, hy - 4), (cx - 20, hy + 2), (cx - 16, hy - 6)], MOCADOR)
    for x in (cx - 6, cx, cx + 6):
        lz.elipse(x, hy - 10, 1.0, 1.0, (250, 230, 200), outline=None)
    # brazos en alto con castanyoles
    for sig in (-1, 1):
        hombro = (cx + sig * 19, 58 + b)
        mano = (cx + sig * 34, 58 + b - br - 10)
        codo = (cx + sig * 30, 62 + b - br * 0.3)
        _brazo(lz, hombro, codo, mano)
        _castanyola(lz, mano[0], mano[1])
    return lz.reducir()


def dibujar_payesa_baila(escala, fase=0, suavizado=4):
    lz = _Lienzo(escala, suavizado, 90, 135)
    f = fase % 4
    b, br = _BOTE[f], _BRAZOS[f]
    vuelo = (8, 18, 8, 3)[f]
    cx, suelo = 45, 133 + b
    cintura = 80 + b
    # zapatos bajo la falda
    for x in (cx - 7, cx + 7):
        lz.elipse(x + 1, suelo - 3, 5.5, 3, SABATA)
        lz.poli([(x - 3, suelo - 12), (x + 3, suelo - 12), (x + 3, suelo - 4), (x - 3, suelo - 4)], CALCES)
    # faldilla de vuelo con flores y davantal
    bajo = suelo - 10
    lz.poli([(cx - 13, cintura), (cx + 13, cintura), (cx + 22 + vuelo, bajo), (cx + 12, bajo + 3),
             (cx, bajo + 1), (cx - 12, bajo + 3), (cx - 22 - vuelo, bajo)], FALDILLA)
    for fila, (dy_f, r_f) in enumerate(((6, 1.6), (15, 1.2))):
        y = bajo - dy_f
        frac = (y - cintura) / (bajo - cintura)          # anchura de la falda a esa altura
        media = 13 + (9 + vuelo) * frac - 2.5
        for i in range(7):
            x = cx - media + (i + 0.5 + 0.5 * fila) / 7.5 * 2 * media
            lz.elipse(x, y, r_f, r_f, FALDILLA_FLOR, outline=None)
    lz.linea([(cx - 22 - vuelo, bajo), (cx + 22 + vuelo, bajo)], FALDILLA_FLOR, 1.4)
    lz.poli([(cx - 9, cintura + 2), (cx + 9, cintura + 2), (cx + 12 + vuelo * 0.3, bajo - 6),
             (cx - 12 - vuelo * 0.3, bajo - 6)], DAVANTAL)
    lz.linea([(cx - 12 - vuelo * 0.3, bajo - 7), (cx + 12 + vuelo * 0.3, bajo - 7)], DAVANTAL_VORA, 1.6)
    # cosset negro con cordones dorados
    lz.poli([(cx - 15, 56 + b), (cx + 15, 56 + b), (cx + 13, cintura + 2), (cx - 13, cintura + 2)], COSSET)
    for i in range(4):
        y = 62 + b + i * 4.5
        lz.linea([(cx - 4, y), (cx + 4, y + 3)], CORDON, 0.9)
        lz.linea([(cx + 4, y), (cx - 4, y + 3)], CORDON, 0.9)
    # brazos en alto con mànigues oscuras y castanyoles
    for sig in (-1, 1):
        hombro = (cx + sig * 14, 60 + b)
        mano = (cx + sig * 31, 58 + b - br - 10)
        codo = (cx + sig * 27, 64 + b - br * 0.3)
        _brazo(lz, hombro, codo, mano, manga=MANIGA)
        _castanyola(lz, mano[0], mano[1])
    # rebosillo: tul blanco que enmarca la cara y cae sobre los hombros
    hy = 38 + b
    lz.poli(_curva((cx - 17, hy + 4), (cx, hy - 28), (cx + 17, hy + 4), 12) +
            [(cx + 19, 58 + b), (cx + 6, 66 + b), (cx, 70 + b), (cx - 6, 66 + b), (cx - 19, 58 + b)], REBOSILLO)
    lz.linea(_curva((cx - 14, 58 + b), (cx, 64 + b), (cx + 14, 58 + b), 8), REBOSILLO_SOMBRA, 1.0)
    _cara(lz, cx, hy, ojos="abiertos", bigote=False, boca="sonrisa", mujer=True)
    # cabello moreno con raya al medio, recogido bajo el rebosillo
    lz.poli(_curva((cx - 11, hy - 3), (cx, hy - 16), (cx + 11, hy - 3), 8) + [(cx + 1, hy - 10), (cx - 1, hy - 10)],
            (52, 34, 28))
    return lz.reducir()
