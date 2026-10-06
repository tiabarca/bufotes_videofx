"""
Ase mallorquí del evento "asnos", con la misma técnica que la cabra
(modulos/sprite_cabra.py): formas planas con contorno, dibujado a más
resolución y reducido.

Pelaje negro con el morro, el anillo de los ojos y la barriga claros ("boca
de farina"), orejas muy largas, crin corta y tiesa. Se dibuja la MITAD
DELANTERA del burro (cabeza, cuello, pecho, patas delanteras y medio cuerpo),
con el cuerpo cortado por el borde izquierdo del lienzo: el evento pega ese
borde al borde de la pantalla, así que se lee como un burro que asoma desde
fuera de cuadro, no como una cabeza suelta.

Lienzo de 180 x 230 unidades, mirando a la derecha, pezuñas en el borde inferior.

    risa 0..1   0 = boca cerrada y orejas tiesas; 1 = carcajada: cabeza echada
                hacia atrás, mandíbula abierta enseñando los dientes, ojos
                cerrados y orejas caídas hacia atrás
    pata 0..1   la pata delantera de este lado se levanta (pataleo de risa)
"""

import math

from PIL import Image, ImageDraw

ANCHO, ALTO = 180, 230
SUELO = 228

PELO = (52, 46, 46)
PELO_LUZ = (84, 76, 74)
PELO_SOMBRA = (34, 30, 30)
CLARO = (206, 196, 182)        # morro, anillo de los ojos y barriga
CLARO_SOMBRA = (170, 158, 144)
LINEA = (20, 16, 16)
OREJA_DENTRO = (150, 120, 118)
BOCA = (110, 36, 46)
LENGUA = (214, 110, 122)
DIENTE = (250, 246, 222)
DIENTE_SOMBRA = (200, 190, 160)
PEZUNA = (26, 22, 22)


class _Lienzo:
    def __init__(self, escala, suavizado):
        self.ss = suavizado
        self.k = escala * suavizado
        self.img = Image.new("RGBA", (int(ANCHO * self.k), int(ALTO * self.k)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.giro = None  # (ángulo, px, py): se aplica a la cabeza mientras está activo

    def t(self, x, y):
        if self.giro:
            a, px, py = self.giro
            c, s = math.cos(a), math.sin(a)
            x, y = px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c
        return x, y

    def p(self, x, y):
        x, y = self.t(x, y)
        return x * self.k, y * self.k

    def poli(self, pts, fill, outline=LINEA, ancho=1.4):
        q = [self.p(x, y) for x, y in pts]
        self.d.polygon(q, fill=fill)
        if outline:
            self.d.line(q + [q[0]], fill=outline, width=max(1, int(ancho * self.k)), joint="curve")

    def elipse(self, cx, cy, rx, ry, fill, outline=LINEA, ancho=1.4, n=40):
        self.poli([(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n))
                   for i in range(n)], fill, outline, ancho)

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
        self.poli(izq + der[::-1], fill, outline, 1.2)

    def reducir(self):
        if self.ss == 1:
            return self.img
        return self.img.resize((self.img.width // self.ss, self.img.height // self.ss), Image.LANCZOS)


def _curva(a, b, c, n=10):
    return [((1 - s) ** 2 * a[0] + 2 * (1 - s) * s * b[0] + s * s * c[0],
             (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * b[1] + s * s * c[1]) for s in (i / n for i in range(n + 1))]


def _crin(lz, borde, n=10, alto=7):
    """Crin corta y tiesa: tira de dientes de sierra pegada al borde superior del cuello.
    borde: lista de puntos del borde, de atrás (izquierda) a la nuca."""
    pts = []
    tramos = list(zip(borde, borde[1:]))
    largos = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in tramos]
    total = sum(largos)
    for i in range(n * 2 + 1):
        d = total * i / (n * 2)
        for (a, b), l in zip(tramos, largos):
            if d <= l or (a, b) == tramos[-1]:
                f = min(1.0, d / l) if l else 0
                x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
                nx, ny = (b[1] - a[1]) / (l or 1), -(b[0] - a[0]) / (l or 1)  # normal hacia fuera (arriba)
                h = alto if i % 2 else 1.5
                pts.append((x + nx * h - 2 * (i % 2), y + ny * h))
                break
            d -= l
    base = [(x, y + 3) for x, y in borde[::-1]]
    lz.poli(pts + base, PELO_SOMBRA, ancho=1.0)


def _pata(lz, cadera, pie, color, levanta=0.0):
    """Pata delantera: brazo ancho, rodilla y caña fina con pezuña. levanta 0..1 la dobla hacia arriba."""
    cx, cy = cadera
    px, py = pie
    rod = (cx + (px - cx) * 0.5 + 10 * levanta, cy + (py - cy) * 0.5 - 4 * levanta)
    py -= 26 * levanta
    px += 14 * levanta
    lz.tubo(_curva((cx, cy), rod, (px, py), 10), [16 - 9 * i / 10 for i in range(11)], color)
    a = math.atan2(py - rod[1], px - rod[0])
    c, s = math.cos(a), math.sin(a)

    def r(u, v):
        return px + u * c - v * s, py + u * s + v * c
    lz.poli([r(-1, -4.2), r(5, -4.6), r(5.4, 4.2), r(-1, 4.6)], PEZUNA)


def _cabeza(lz, risa):
    # --- cabeza: gira alrededor de la nuca al reír (se echa hacia atrás)
    lz.giro = (math.radians(-20 * risa), 124.0, 86.0)
    caida = 22 * risa  # orejas hacia atrás con la carcajada
    for dx, col in ((8, PELO_SOMBRA), (0, PELO)):  # orejas: la de detrás primero
        base = (124 + dx, 60)
        punta = (110 + dx - caida, 8 + caida * 0.6)
        oreja = _curva(base, (106 + dx - caida * 0.5, 34), punta, 8) + \
            _curva((punta[0] + 8, punta[1] + 2), (122 + dx - caida * 0.3, 32), (134 + dx, 62), 8)
        lz.poli(oreja, col)
        if col == PELO:
            lz.poli(_curva((124, 56), (112 - caida * 0.5, 34), (114 - caida, 16 + caida * 0.6), 6) +
                    _curva((118 - caida, 18 + caida * 0.6), (122 - caida * 0.3, 36), (130, 58), 6),
                    OREJA_DENTRO, outline=None)
    lz.elipse(132, 70, 21, 18, PELO, ancho=1.5)  # cráneo
    # mandíbula inferior: se abre girando sobre la bisagra
    abre = math.radians(30 * risa)
    bis = (140.0, 94.0)

    def mand(x, y):
        c, s = math.cos(abre), math.sin(abre)
        return bis[0] + (x - bis[0]) * c - (y - bis[1]) * s, bis[1] + (x - bis[0]) * s + (y - bis[1]) * c

    if risa > 0.15:  # boca por dentro, lengua y dientes de abajo
        lz.poli([(140, 92), (172, 90), mand(170, 100), mand(140, 100)], BOCA)
        lz.elipse(*mand(156, 99), 9, 3.2, LENGUA, ancho=0.9)
    lz.poli([mand(138, 94), mand(168, 96), mand(166, 106), mand(150, 110), mand(138, 104)], CLARO)
    if risa > 0.15:
        for i in range(4):
            x = 148 + i * 5
            lz.poli([mand(x, 97), mand(x + 4.4, 97), mand(x + 4.2, 101), mand(x + 0.2, 101)], DIENTE,
                    ancho=0.7)
    # hocico superior, largo y claro
    lz.poli([(136, 58), (160, 66), (176, 80), (176, 92), (140, 96), (130, 84)], PELO)
    lz.poli([(150, 72), (166, 74), (178, 82), (177, 93), (146, 96), (144, 84)], CLARO)
    lz.elipse(171, 82, 2.2, 3.2, CLARO_SOMBRA, ancho=1.0)  # orificio nasal
    if risa > 0.15:  # dientes de arriba, grandes: la carcajada de burro
        for i in range(5):
            x = 146 + i * 5.6
            lz.poli([(x, 92), (x + 5, 92), (x + 4.8, 99), (x + 0.2, 99)], DIENTE, ancho=0.7)
            lz.linea([(x + 0.8, 97.5), (x + 4.2, 97.5)], DIENTE_SOMBRA, 0.6)
    else:
        lz.linea(_curva((144, 96), (156, 99), (170, 95), 6), LINEA, 1.4)  # boca cerrada
    # ojo con anillo claro; cerrado de risa
    lz.elipse(136, 64, 7, 6, CLARO, outline=None)
    if risa > 0.5:
        lz.linea(_curva((131, 64), (136, 60), (141, 64), 6), LINEA, 1.8)
        lz.linea([(129, 70), (131, 74)], (150, 200, 240), 1.4)  # lagrimita de risa
    else:
        lz.elipse(136, 64, 4.2, 4.2, (250, 250, 250), ancho=1.0)
        lz.elipse(137.5, 64.5, 2.2, 2.6, LINEA, outline=None)
        lz.elipse(138.2, 63.4, 0.8, 0.8, (255, 255, 255), outline=None)
    lz.poli(_curva((120, 56), (128, 44), (138, 50), 6) + [(132, 58)], PELO_SOMBRA)  # tupé
    lz.giro = None


CABEZA_X0, CABEZA_Y1 = 70, 150  # recorte de solo_cabeza: de x=70 a la derecha y de y=0 a 150


def dibujar(escala, risa=0.0, pata=0.0, suavizado=4, solo_cabeza=False):
    """
    solo_cabeza=True: solo cabeza y un trozo de cuello, recortado a un lienzo de
    110 x 150 unidades (x 70..180, y 0..150). El cuello llega hasta el borde izquierdo:
    pegado al borde de la pantalla, es un burro asomando la cabeza desde fuera de cuadro.
    """
    lz = _Lienzo(escala, suavizado)
    if solo_cabeza:
        # cuello que sale de fuera de cuadro (por la izquierda) hasta la nuca
        lz.poli([(CABEZA_X0 - 4, 104), (96, 98), (120, 80), (138, 92), (128, 124), (CABEZA_X0 - 4, 142)], PELO)
        lz.poli([(CABEZA_X0 - 4, 132), (110, 126), (126, 118), (124, 128), (CABEZA_X0 - 4, 142)], PELO_SOMBRA,
                outline=None)
        _crin(lz, [(CABEZA_X0 - 4, 104), (96, 98), (121, 80)])
        _cabeza(lz, risa)
        img = lz.reducir()
        return img.crop((int(CABEZA_X0 * escala), 0, img.width, int(CABEZA_Y1 * escala)))

    # --- pata delantera del lado de allá
    _pata(lz, (86, 168), (82, SUELO - 4), PELO_SOMBRA)

    # --- medio cuerpo, cortado por el borde izquierdo del lienzo (fuera de cuadro)
    lz.poli([(-4, 112)] + _curva((-4, 112), (50, 104), (96, 128), 10)[1:] + [(112, 160), (100, 188)] +
            _curva((96, 186), (50, 196), (-4, 190), 10)[1:], PELO)
    lz.poli(_curva((-4, 176), (40, 190), (88, 180), 10) + [(84, 188)] + _curva((80, 189), (40, 196), (-4, 189), 6),
            CLARO, outline=None)  # barriga clara
    lz.poli(_curva((-4, 118), (40, 110), (80, 124), 8) + [(70, 130), (-4, 128)], PELO_LUZ, outline=None)  # lomo

    # --- cuello hacia arriba y delante, con la crin tiesa
    lz.poli([(78, 130), (96, 108), (120, 80), (138, 92), (124, 132), (112, 162), (92, 158)], PELO)
    _crin(lz, [(90, 114), (96, 108), (121, 80)], n=8)

    _cabeza(lz, risa)

    # --- pata delantera del lado de acá (pataleo de risa)
    _pata(lz, (102, 170), (104, SUELO - 4), PELO, levanta=pata)
    return lz.reducir()
