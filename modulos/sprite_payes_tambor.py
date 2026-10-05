"""
Dibujo del músico del evento "cabra": un flabioler mallorquín con la ropa
tradicional de pagès (barret negro de ala ancha, camisa blanca, armilla,
faixa roja, calçons de bufa, calces blancas y espardenyes), tocando a la vez
el flabiol con una mano y el tamborí con la otra, como se hace de verdad.

Lienzo de 100 x 130 unidades, de pie con los pies en el borde inferior y el
tamborí a su izquierda (a la derecha del dibujo), que es el lado por el que
le llega la coz de la cabra. Para que el tamborí mire al otro lado basta con
espejar la imagen.

    fase 0 / 1   la baqueta arriba / abajo (alternando rápido: el redoble)
    golpe=True   el instante de la coz: el tamborí sale despedido y chispea,
                 el músico se encoge con los ojos como platos, el barret
                 salta y el flabiol se le escapa de la boca
"""

import math

from PIL import Image, ImageDraw

ANCHO, ALTO = 100, 130

LINEA = (28, 22, 20)
PIEL = (232, 186, 152)
PIEL_SOMBRA = (206, 156, 124)
MEJILLA = (226, 140, 120)
CAMISA = (244, 240, 230)
CAMISA_SOMBRA = (214, 208, 196)
ARMILLA = (36, 52, 46)
ARMILLA_LUZ = (58, 78, 70)
BOTON = (214, 180, 90)
FAIXA = (176, 40, 40)
CALCONS = (44, 50, 70)
CALCONS_LUZ = (64, 72, 96)
CALCES = (236, 232, 222)
ESPARDENYA = (214, 194, 150)
CINTA = (40, 34, 30)
BARRET = (30, 28, 30)
BARRET_LUZ = (58, 54, 58)
BIGOTE = (150, 146, 140)
MADERA = (136, 92, 54)
MADERA_OSC = (96, 62, 36)
CAJA = (186, 54, 46)       # caja del tamborí, pintada
CAJA_DECO = (236, 196, 80)
PARCHE = (234, 222, 196)
CUERDA = (240, 236, 220)


class _Lienzo:
    def __init__(self, escala, suavizado):
        self.ss = suavizado
        self.k = escala * suavizado
        self.img = Image.new("RGBA", (int(ANCHO * self.k), int(ALTO * self.k)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.dx, self.dy = 0.0, 0.0  # desplazamiento del torso (el encogimiento del golpe)

    def p(self, x, y):
        return x * self.k, y * self.k

    def poli(self, pts, fill, outline=LINEA, ancho=1.3):
        q = [self.p(x, y) for x, y in pts]
        self.d.polygon(q, fill=fill)
        if outline:
            self.d.line(q + [q[0]], fill=outline, width=max(1, int(ancho * self.k)), joint="curve")

    def elipse(self, cx, cy, rx, ry, fill, outline=LINEA, ancho=1.3, a0=0, a1=360, n=40):
        pts = []
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
        self.poli(pts, fill, outline, ancho)

    def linea(self, pts, color, ancho):
        self.d.line([self.p(x, y) for x, y in pts], fill=color, width=max(1, int(ancho * self.k)), joint="curve")

    def tubo(self, pts, anchos, fill, outline=LINEA):
        izq, der = [], []
        for i, (x, y) in enumerate(pts):
            x0, y0 = pts[max(0, i - 1)]
            x1, y1 = pts[min(len(pts) - 1, i + 1)]
            n = math.hypot(x1 - x0, y1 - y0) or 1.0
            nx, ny = -(y1 - y0) / n, (x1 - x0) / n
            w = anchos[i] / 2
            izq.append((x + nx * w, y + ny * w))
            der.append((x - nx * w, y - ny * w))
        self.poli(izq + der[::-1], fill, outline, 1.1)

    def reducir(self):
        if self.ss == 1:
            return self.img
        return self.img.resize((self.img.width // self.ss, self.img.height // self.ss), Image.LANCZOS)


def _curva(a, b, c, n=10):
    return [((1 - s) ** 2 * a[0] + 2 * (1 - s) * s * b[0] + s * s * c[0],
             (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * b[1] + s * s * c[1]) for s in (i / n for i in range(n + 1))]


def _estallido(lz, cx, cy, r0=5, r1=20, n=9):
    for i in range(n):
        a = math.radians(i * 360 / n + 8)
        lz.linea([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                  (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], (255, 240, 170), 2.4)
    lz.elipse(cx, cy, 4, 4, (255, 250, 214), outline=None)


def _tambori(lz, cx, cy, inclina=0.0):
    """Tamborí visto un poco desde arriba: caja cilíndrica pintada, parche y cuerdas en zigzag."""
    rx, ry, alto = 15, 5.5, 18
    c, s = math.cos(inclina), math.sin(inclina)

    def r(x, y):
        return cx + x * c - y * s, cy + x * s + y * c

    caja = [r(-rx, 0)] + [r(rx * math.cos(math.radians(a)), ry * math.sin(math.radians(a)) + alto)
                          for a in range(180, -1, -10)][::-1] + [r(rx, 0)]
    caja = [r(-rx, 0), r(-rx, alto)] + [r(rx * math.cos(math.radians(a)), alto + ry * math.sin(math.radians(a)))
                                        for a in range(180, -1, -15)] + [r(rx, alto), r(rx, 0)]
    lz.poli(caja, CAJA)
    for i in range(7):  # cuerdas en zigzag
        x0 = -rx + i * (2 * rx / 6)
        x1 = -rx + (i + 0.5) * (2 * rx / 6)
        if x1 <= rx:
            lz.linea([r(x0, 2), r(x1, alto - 2)], CUERDA, 1.0)
            lz.linea([r(x1, alto - 2), r(min(rx, x1 + rx / 6), 2)], CUERDA, 1.0)
    lz.linea([r(-rx, alto * 0.5), r(rx, alto * 0.5)], CAJA_DECO, 1.2)  # franja pintada
    # aro y parche
    lz.poli([r(rx * math.cos(math.radians(a)), ry * math.sin(math.radians(a))) for a in range(0, 360, 12)],
            PARCHE, ancho=1.4)
    lz.elipse(*r(-4, -1), 3.5, 1.2, (246, 238, 220), outline=None)  # brillo del parche


def dibujar(escala, fase=0, golpe=False, suavizado=4):
    lz = _Lienzo(escala, suavizado)
    arriba = fase % 2 == 0
    sube = 4 if golpe else 0        # el cuerpo da un respingo
    dy = -sube

    # --- piernas: calces blancas, espardenyes con cintas
    for x in (40, 58):
        lz.poli([(x - 5, 108), (x + 5, 108), (x + 4, 122), (x - 4, 122)], CALCES)
        for yy in (113, 117):
            lz.linea([(x - 4.5, yy), (x + 4.5, yy + 2)], CINTA, 0.8)
        lz.elipse(x + 1, 125, 7, 3.5, ESPARDENYA)
        lz.linea([(x - 4, 123), (x + 3, 121)], CINTA, 1.0)
    # calçons de bufa (anchos, recogidos bajo la rodilla)
    lz.poli([(32, 88 + dy), (68, 88 + dy), (70, 102), (64, 110), (52, 108), (49, 100), (46, 108),
             (34, 110), (29, 102)], CALCONS)
    lz.linea(_curva((40, 92 + dy), (38, 100), (40, 106), 6), CALCONS_LUZ, 1.6)
    lz.linea(_curva((58, 92 + dy), (60, 100), (58, 106), 6), CALCONS_LUZ, 1.6)

    # --- torso: camisa blanca, armilla oscura con botones, faixa roja
    lz.poli([(28, 50 + dy), (72, 50 + dy), (74, 86 + dy), (26, 86 + dy)], CAMISA)
    lz.poli([(30, 52 + dy), (45, 52 + dy), (47, 86 + dy), (28, 86 + dy)], ARMILLA)
    lz.poli([(55, 52 + dy), (70, 52 + dy), (72, 86 + dy), (53, 86 + dy)], ARMILLA)
    lz.linea([(32, 56 + dy), (34, 82 + dy)], ARMILLA_LUZ, 1.4)
    for i in range(4):
        lz.elipse(51 - 6.2, 58 + i * 6.5 + dy, 1.1, 1.1, BOTON, ancho=0.6)
        lz.elipse(51 + 6.2, 58 + i * 6.5 + dy, 1.1, 1.1, BOTON, ancho=0.6)
    lz.poli([(26, 84 + dy), (74, 84 + dy), (74, 91 + dy), (26, 91 + dy)], FAIXA)
    lz.poli([(64, 89 + dy), (70, 89 + dy), (72, 100 + dy), (66, 99 + dy)], FAIXA)  # caída de la faixa
    # correa del tamborí, en bandolera
    lz.linea([(36, 51 + dy), (66, 74 + dy)], (120, 84, 50), 2.2)

    # --- tamborí colgado a su izquierda (derecha del dibujo)
    if golpe:
        tx, ty, inc = 80, 56, math.radians(-22)  # sale despedido hacia arriba y se ladea
    else:
        tx, ty, inc = 80, 68 + dy, math.radians(-6)
    _tambori(lz, tx, ty, inc)

    # --- cabeza
    hy = 30 + dy - (2 if golpe else 0)
    lz.elipse(50, hy, 13, 14, PIEL)
    lz.elipse(37.5, hy + 1, 2.6, 3.6, PIEL_SOMBRA, ancho=1.0)  # oreja
    lz.elipse(43, hy + 6, 3.2, 2.2, MEJILLA, outline=None)
    lz.elipse(58, hy + 6, 3.2, 2.2, MEJILLA, outline=None)
    if golpe:  # ojos como platos
        for x in (45, 56):
            lz.elipse(x, hy - 1, 3.4, 3.8, (255, 255, 255), ancho=0.9)
            lz.elipse(x, hy - 1, 1.2, 1.2, LINEA, outline=None)
        lz.linea([(41, hy - 7), (48, hy - 8)], LINEA, 1.1)
        lz.linea([(53, hy - 8), (60, hy - 7)], LINEA, 1.1)
    else:  # concentrado tocando: ojos entornados, cejas arqueadas
        for x in (45, 56):
            lz.linea([(x - 2.6, hy - 1), (x + 2.6, hy - 1)], LINEA, 1.4)
        lz.linea([(41, hy - 6), (48, hy - 5)], BIGOTE, 1.4)
        lz.linea([(53, hy - 5), (60, hy - 6)], BIGOTE, 1.4)
    lz.elipse(51, hy + 3, 3.2, 4.2, PIEL_SOMBRA, ancho=1.0)  # nariz
    # bigote canoso
    lz.poli(_curva((42, hy + 9), (50, hy + 5), (58, hy + 9), 8) + _curva((56, hy + 11), (50, hy + 8.5), (44, hy + 11), 8),
            BIGOTE, ancho=1.0)
    if golpe:
        lz.elipse(50, hy + 12, 2.6, 2.4, (120, 40, 50), ancho=0.9)  # boca abierta del susto

    # --- barret negro de ala ancha (salta en el golpe)
    by = hy - 11 - (7 if golpe else 0)
    ang = math.radians(-12 if golpe else -4)
    c, s = math.cos(ang), math.sin(ang)

    def rb(x, y):
        return 50 + x * c - y * s, by + x * s + y * c

    lz.poli([rb(-21, 1), rb(21, 1), rb(19, 4), rb(-19, 4)], BARRET)                    # ala
    lz.poli([rb(-11, 2), rb(-10, -9), rb(-4, -11), rb(4, -11), rb(10, -9), rb(11, 2)], BARRET)  # copa
    lz.poli([rb(-11, -1), rb(11, -1), rb(11, 2), rb(-11, 2)], BARRET_LUZ, outline=None)  # cinta

    # --- brazo izquierdo del dibujo (su derecha): sujeta el flabiol, que va de la boca hacia abajo
    hombro = (31, 55 + dy)
    if golpe:
        codo, mano = (20, 58 + dy), (22, 46 + dy)
        flab = [(16, 36), (30, 52)]  # se le escapa de la boca
    else:
        codo, mano = (22, 68 + dy), (39, 62 + dy)
        flab = [(49, hy + 11), (36, 66 + dy)]
    lz.tubo([hombro, codo, mano], [9, 8, 6.5], CAMISA)
    lz.tubo([flab[0], ((flab[0][0] + flab[1][0]) / 2, (flab[0][1] + flab[1][1]) / 2), flab[1]], [2.8, 2.5, 2.3],
            MADERA)
    for j in (0.45, 0.6, 0.75):  # agujeros del flabiol
        lz.elipse(flab[0][0] + (flab[1][0] - flab[0][0]) * j, flab[0][1] + (flab[1][1] - flab[0][1]) * j,
                  0.6, 0.6, MADERA_OSC, outline=None)
    lz.elipse(mano[0], mano[1], 4.2, 3.6, PIEL)

    # --- brazo derecho del dibujo (su izquierda): la baqueta del redoble
    hombro2 = (70, 55 + dy)
    if golpe:
        mano2 = (82, 46)
        punta = (94, 34)
    elif arriba:
        mano2 = (78, 52 + dy)
        punta = (90, 40 + dy)
    else:
        mano2 = (80, 60 + dy)
        punta = (86, 66 + dy)  # justo en el parche
    codo2 = (80, 64 + dy) if not golpe else (80, 58)
    lz.tubo([hombro2, codo2, mano2], [9, 8, 6.5], CAMISA)
    lz.tubo([mano2, ((mano2[0] + punta[0]) / 2, (mano2[1] + punta[1]) / 2), punta], [2.4, 2.0, 1.6], MADERA_OSC)
    lz.elipse(punta[0], punta[1], 1.8, 1.8, MADERA_OSC, ancho=0.8)
    lz.elipse(mano2[0], mano2[1], 4.2, 3.6, PIEL)
    if not arriba and not golpe:  # chasquido del parche
        for a in (-60, -100, -140):
            ra = math.radians(a)
            lz.linea([(punta[0] + math.cos(ra) * 4, punta[1] + math.sin(ra) * 4),
                      (punta[0] + math.cos(ra) * 7, punta[1] + math.sin(ra) * 7)], (255, 244, 190), 1.2)

    if golpe:
        _estallido(lz, tx, ty + 4)
    return lz.reducir()
