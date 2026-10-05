"""
Dibujo de la cabra mallorquina del evento "cabra": negra, de pelo largo con
flecos en la barriga, barba, ojos amarillos de pupila horizontal y cuernos
grandes en arco hacia atrás.

La usa eventos_extra.dibujar_cabra() y también crear_sprites_cabra.py, que
la vuelca a PNG para retocarla a mano.

Lienzo de 110 x 160 unidades, mirando a la derecha, pezuñas en el borde
inferior. En la coz el cuerpo bascula sobre las patas delanteras y las
traseras salen disparadas hacia atrás, a la altura del tamborí del payès.
"""

import math

from PIL import Image, ImageDraw

PASOS_COZ = (0.0, 0.25, 0.5, 0.7, 0.85, 1.0)  # los mismos que _PASOS_COZ de eventos_extra.py
ANCHO, ALTO = 110, 160                        # lienzo en unidades de diseño
SUELO = 157                                   # y de la planta de las pezuñas

# paleta
PELO = (48, 40, 38)
PELO_LUZ = (78, 66, 60)
PELO_SOMBRA = (34, 28, 27)
LINEA = (20, 16, 16)
MORRO = (96, 84, 78)
CUERNO = (205, 186, 148)
CUERNO_SOMBRA = (160, 138, 100)
PEZUNA = (28, 24, 22)
OJO = (232, 190, 70)


ESCALA_FIG = 0.85            # la cabra se dibuja algo más pequeña que el lienzo...
ANCLA_FIG = (100.0, SUELO)   # ...anclada abajo a la derecha, para que quepa la coz hacia atrás


class Lienzo:
    def __init__(self, escala, suavizado):
        self.ss = suavizado
        self.k = escala * suavizado
        self.img = Image.new("RGBA", (int(ANCHO * self.k), int(ALTO * self.k)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.giro = (0.0, 0.0, 0.0)  # (ángulo, pivote x, pivote y) aplicado al cuerpo
        self.retroceso = 0.0         # desplazamiento del cuerpo hacia atrás (en la coz)

    # -- transformaciones
    def t(self, x, y):
        """Gira un punto del cuerpo alrededor del pivote (para inclinarlo en la coz)."""
        a, px, py = self.giro
        if a:
            c, s = math.cos(a), math.sin(a)
            x, y = px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c
        return x - self.retroceso, y

    def p(self, x, y, girar=True):
        if girar:
            x, y = self.t(x, y)
        ax, ay = ANCLA_FIG
        x, y = ax + (x - ax) * ESCALA_FIG, ay + (y - ay) * ESCALA_FIG
        return x * self.k, y * self.k

    # -- primitivas
    def poli(self, pts, fill, outline=LINEA, ancho=1.4, girar=True):
        self.d.polygon([self.p(x, y, girar) for x, y in pts], fill=fill)
        if outline:
            q = [self.p(x, y, girar) for x, y in pts]
            self.d.line(q + [q[0]], fill=outline, width=max(1, int(ancho * self.k)), joint="curve")

    def elipse(self, cx, cy, rx, ry, fill, outline=LINEA, ancho=1.4, girar=True, n=40):
        pts = [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
        self.poli(pts, fill, outline, ancho, girar)

    def linea(self, pts, color, ancho, girar=True):
        self.d.line([self.p(x, y, girar) for x, y in pts], fill=color, width=max(1, int(ancho * self.k)),
                    joint="curve")

    def tubo(self, pts, anchos, fill, outline=LINEA, girar=True):
        """Trazo grueso que se estrecha: un polígono alrededor de la polilínea."""
        izq, der = [], []
        for i, (x, y) in enumerate(pts):
            x0, y0 = pts[max(0, i - 1)]
            x1, y1 = pts[min(len(pts) - 1, i + 1)]
            dx, dy = x1 - x0, y1 - y0
            n = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / n, dx / n
            w = anchos[i] / 2
            izq.append((x + nx * w, y + ny * w))
            der.append((x - nx * w, y - ny * w))
        self.poli(izq + der[::-1], fill, outline, 1.2, girar)

    def reducir(self):
        if self.ss == 1:
            return self.img
        return self.img.resize((self.img.width // self.ss, self.img.height // self.ss), Image.LANCZOS)


def _curva(a, b, c, n=12):
    """Bézier cuadrática de a a c con control b."""
    out = []
    for i in range(n + 1):
        s = i / n
        out.append(((1 - s) ** 2 * a[0] + 2 * (1 - s) * s * b[0] + s * s * c[0],
                    (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * b[1] + s * s * c[1]))
    return out


def _pata(lz, cadera, rodilla, pezuna, color, girar_cadera=True):
    """Pata en dos tramos (muslo y caña) con pezuña. La cadera va pegada al cuerpo (girada con él);
    la rodilla y la pezuña se dan ya en coordenadas finales."""
    cx, cy = lz.t(*cadera) if girar_cadera else cadera
    puntos = _curva((cx, cy), rodilla, pezuna, 10)
    anchos = [10 - 5 * i / 10 for i in range(11)]
    lz.tubo(puntos, anchos, color, girar=False)
    # pezuña: hacia delante del sentido de la caña
    px, py = pezuna
    rx, ry = rodilla
    a = math.atan2(py - ry, px - rx)
    c, s = math.cos(a), math.sin(a)
    def r(u, v):
        return px + u * c - v * s, py + u * s + v * c
    lz.poli([r(-2, -3.2), r(3.2, -3.4), r(3.6, 3.0), r(-2, 3.4)], PEZUNA, girar=False)


def _estallido(lz, cx, cy, r0=4, r1=18, n=8):
    for i in range(n):
        a = math.radians(i * 360 / n + 10)
        lz.linea([(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                  (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], (255, 240, 170), 2.6, girar=False)
    lz.elipse(cx, cy, 4, 4, (255, 250, 210), outline=None, girar=False)


def dibujar(escala, fase, impacto=False, suavizado=4):
    """
    Cabra de perfil mirando a la derecha, en un lienzo de 110 x 160 unidades
    (escala = píxeles por unidad). fase 0 = de pie; 1 = coz en todo lo alto.
    impacto=True añade el estallido en las pezuñas. suavizado: se dibuja a
    esa resolución extra y se reduce, para que los bordes queden finos.
    """
    lz = Lienzo(escala, suavizado)
    # en la coz el cuerpo bascula sobre las patas delanteras: la grupa sube y la cabeza baja
    lz.giro = (math.radians(9 * fase), 72.0, 150.0)
    lz.retroceso = 9 * fase  # la cabeza no se sale del lienzo al inclinarse

    # patas traseras: giran alrededor de la cadera desde "hacia abajo" (de pie) hasta casi
    # horizontales hacia atrás (la coz). A media coz se recogen, para coger impulso.
    pez_tras, rod_tras = [], []
    ang = math.radians(95 + 125 * fase)           # 90 = hacia abajo, 180 = hacia atrás, 220 = atrás y arriba
    largo = 33 - 13 * math.sin(math.pi * min(1.0, fase / 0.8)) + 3 * fase
    for i in range(2):
        cx, cy = lz.t(28 + 10 * i, 122)
        dx, dy = math.cos(ang), math.sin(ang)
        px, py = cx + dx * largo, cy + dy * largo
        if fase == 0:
            py = SUELO - 3  # de pie, bien plantada en el suelo
        pez_tras.append((px, py))
        doble = 5 * (1 - fase) + 9 * math.sin(math.pi * min(1.0, fase / 0.8))  # corvejón
        mx, my = cx + dx * largo * 0.5, cy + dy * largo * 0.5
        rod_tras.append((mx - dy * doble, my + dx * doble))

    # --- lado lejano (más oscuro): pata delantera y trasera de atrás
    _pata(lz, (78, 124), (80, 140), (80, SUELO - 3), PELO_SOMBRA)
    _pata(lz, (38, 122), rod_tras[1], pez_tras[1], PELO_SOMBRA)

    # --- cola: un mechón hacia arriba (más tiesa en la coz)
    lz.tubo(_curva((20, 104), (12, 96 - 6 * fase), (10, 86 - 8 * fase), 8), [7, 6, 5, 4, 4, 3, 3, 2, 1.5],
            PELO)

    # --- cuerpo con flecos de pelo largo en la barriga
    flecos = []
    for i in range(13):
        x = 20 + i * 5
        flecos.append((x, 124 + (3 if i % 2 else 9)))
    cuerpo = [(16, 112)] + _curva((16, 104), (40, 88), (82, 98), 10)[1:] + [(88, 112), (84, 124)]
    cuerpo += flecos[::-1] + [(18, 122)]
    lz.poli(cuerpo, PELO)
    lz.poli(_curva((26, 100), (44, 92), (70, 98), 8) + [(64, 104), (30, 106)], PELO_LUZ, outline=None)  # brillo del lomo
    for i in range(5):  # mechones dibujados
        x = 30 + i * 11
        lz.linea(_curva((x, 108), (x - 2, 114), (x - 1, 121), 6), PELO_SOMBRA, 1.2)

    # --- cuello y cabeza (bajan en la coz por el giro del cuerpo)
    lz.poli([(74, 100), (86, 84), (98, 88), (92, 112), (82, 118)], PELO)
    # oreja caída hacia atrás
    lz.poli(_curva((88, 82), (80, 84), (72, 94), 6) + _curva((74, 96), (84, 90), (92, 88), 6), PELO_SOMBRA)
    # cuernos grandes en arco hacia atrás (primero el de detrás, más oscuro)
    for dx, col in ((5, CUERNO_SOMBRA), (0, CUERNO)):
        arco = _curva((92 + dx, 76), (86 + dx, 48), (64 + dx, 60), 14)
        lz.tubo(arco, [7.5 - 6 * i / 14 for i in range(15)], col)
        for j in range(3, 12, 3):  # anillos del cuerno
            x, y = arco[j]
            lz.linea([(x - 2.4, y - 1.5), (x + 2.4, y + 1.5)], CUERNO_SOMBRA if col == CUERNO else (120, 100, 70), 1.0)
    # cabeza alargada con morro gris
    lz.poli(_curva((86, 78), (96, 70), (104, 80), 8) + [(110, 92), (108, 99)] +
            _curva((104, 101), (96, 98), (88, 94), 6), PELO)
    lz.poli([(100, 86), (110, 92), (108, 99), (103, 101), (98, 96)], MORRO, outline=None)
    lz.elipse(107, 93, 1.4, 1.0, LINEA, outline=None)   # orificio nasal
    lz.linea([(103, 99), (108, 98)], LINEA, 1.0)       # boca
    # barba
    lz.poli([(98, 98), (104, 101), (101, 114), (99, 108)], PELO_SOMBRA)
    # ojo de cabra: iris amarillo y pupila horizontal
    lz.elipse(95, 83, 3.2, 2.6, OJO, ancho=0.9)
    lz.poli([(92.6, 82.4), (97.4, 82.4), (97.4, 83.6), (92.6, 83.6)], LINEA, outline=None)
    if impacto or fase > 0.6:  # cara de esfuerzo: ceja fruncida
        lz.linea([(91, 78.5), (98, 80.5)], LINEA, 1.4)

    # --- lado cercano: pata delantera y trasera de delante
    _pata(lz, (68, 124), (66, 140), (66, SUELO - 3), PELO)
    _pata(lz, (28, 122), rod_tras[0], pez_tras[0], PELO)

    if impacto:
        hx = min(pez_tras[0][0], pez_tras[1][0]) - 3  # justo detrás de las pezuñas
        hy = (pez_tras[0][1] + pez_tras[1][1]) / 2
        _estallido(lz, hx, hy)
    return lz.reducir()
