"""
Las dos ranas protagonistas, con la misma técnica que la cabra
(modulos/sprite_cabra.py): formas planas con contorno oscuro, dibujadas a
más resolución y reducidas con LANCZOS.

Inspiradas en el sapo verde balear (Bufotes balearicus): cuerpo rechoncho,
piel clara (crema/gris oliva) con manchas verdes irregulares ribeteadas de
oscuro, verrugas pequeñas (algunas rojizas), glándulas parotoides alargadas
detrás de los ojos, iris dorado con la pupila horizontal y barriga
blanquecina. Siguen siendo personajes de dibujo: ojos grandes y boca ancha
para que se lea bien el lip-sync.

Mismo lienzo que personajes.rana_generada (360 x (360 + OY) unidades, pies
en el borde inferior), así que el resto del programa no cambia.

    color      tono de las manchas (cada rana el suyo); la piel sale de mezclarlo con crema
    boca       0-6 (ver personajes.GEOM_BOCA)
    postura    0 sentada · 1 agachada (coger impulso / aterrizar)
               2 en el aire (patas traseras estiradas) · 3 erguida (estirándose)
"""

import math
import random

from PIL import Image, ImageChops, ImageDraw

OY = 120                 # margen superior para el sombrero (igual que personajes.OY)
ANCHO, ALTO = 360, 360 + OY
SUELO = 338              # planta de los pies en postura sentada
SS = 3                   # sobremuestreo

LINEA = (28, 24, 20)
CREMA = (226, 220, 192)
BARRIGA = (240, 236, 218)
BARRIGA_SOMBRA = (210, 204, 180)
VERRUGA_ROJA = (196, 104, 72)
IRIS = (214, 172, 58)
IRIS_OSCURO = (128, 94, 30)
PUPILA = (16, 14, 12)
BOCA_DENTRO = (104, 30, 40)
LENGUA = (226, 112, 122)

POSTURAS = (0, 1, 2, 3)

# forma de cada postura: escala del cuerpo, desplazamiento de la cabeza,
# base del cuerpo (y donde apoya) y si las patas traseras van estiradas
_FORMA = {
    0: dict(sx=1.00, sy=1.00, cab=0, base=SUELO, salto=False),
    1: dict(sx=1.09, sy=0.86, cab=26, base=SUELO, salto=False),
    2: dict(sx=0.90, sy=1.06, cab=-46, base=SUELO - 44, salto=True),
    3: dict(sx=0.95, sy=1.08, cab=-18, base=SUELO, salto=False),
}


def _mezcla(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


def _oscurecer(c, f):
    return tuple(max(0, int(v * f)) for v in c)


def _elipse(cx, cy, rx, ry, rot=0.0, n=48):
    c, s = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return pts


def _curva(a, b, c, n=12):
    return [((1 - s) ** 2 * a[0] + 2 * (1 - s) * s * b[0] + s * s * c[0],
             (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * b[1] + s * s * c[1]) for s in (i / n for i in range(n + 1))]


def _tubo(pts, anchos):
    izq, der = [], []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(0, i - 1)]
        x1, y1 = pts[min(len(pts) - 1, i + 1)]
        n = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / n, (x1 - x0) / n
        w = anchos[i] / 2
        izq.append((x + nx * w, y + ny * w))
        der.append((x - nx * w, y - ny * w))
    return izq + der[::-1]


def _mancha(rng, cx, cy, r, n=11):
    """Contorno irregular de una mancha (radio que oscila suave)."""
    fases = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    amp = [rng.uniform(0.08, 0.2), rng.uniform(0.05, 0.15), rng.uniform(0.03, 0.1)]
    alarg = rng.uniform(0.7, 1.3)
    giro = rng.uniform(0, math.pi)
    pts = []
    for i in range(n * 2):
        a = 2 * math.pi * i / (n * 2)
        rr = r * (1 + sum(amp[j] * math.sin((j + 2) * a + fases[j]) for j in range(3)))
        x, y = rr * math.cos(a) * alarg, rr * math.sin(a) / alarg
        c, s = math.cos(giro), math.sin(giro)
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return pts


class _Lienzo:
    def __init__(self, escala):
        self.k = escala * SS
        self.tam = (int(ANCHO * self.k), int(ALTO * self.k))
        self.img = Image.new("RGBA", self.tam, (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def p(self, x, y):
        return x * self.k, (y + OY) * self.k

    def q(self, pts):
        return [self.p(x, y) for x, y in pts]

    def poli(self, pts, fill, outline=LINEA, ancho=2.2, d=None):
        d = d or self.d
        q = self.q(pts)
        d.polygon(q, fill=fill)
        if outline:
            d.line(q + [q[0]], fill=outline, width=max(1, int(ancho * self.k)), joint="curve")

    def linea(self, pts, color, ancho, d=None):
        (d or self.d).line(self.q(pts), fill=color, width=max(1, int(ancho * self.k)), joint="curve")

    def punto(self, x, y, r, color, d=None):
        x, y = self.p(x, y)
        r *= self.k
        (d or self.d).ellipse([x - r, y - r, x + r, y + r], fill=color)

    def grupo(self, formas, piel, decorar=None, ancho=2.6):
        """
        Varias formas que se leen como una sola pieza: un único contorno
        exterior (sin costuras entre ellas) y la decoración (manchas,
        verrugas, barriga) recortada a su interior.
        """
        contorno = Image.new("RGBA", self.tam, (0, 0, 0, 0))
        dc = ImageDraw.Draw(contorno)
        relleno = Image.new("RGBA", self.tam, (0, 0, 0, 0))
        dr = ImageDraw.Draw(relleno)
        w = max(1, int(ancho * 2 * self.k))
        for pts in formas:
            q = self.q(pts)
            dc.polygon(q, fill=LINEA)
            dc.line(q + [q[0]], fill=LINEA, width=w, joint="curve")
        for pts in formas:
            dr.polygon(self.q(pts), fill=piel)
        self.img.alpha_composite(contorno)
        if decorar:
            deco = relleno.copy()
            decorar(ImageDraw.Draw(deco))
            relleno = Image.composite(deco, relleno, relleno.getchannel("A"))
        self.img.alpha_composite(relleno)
        self.d = ImageDraw.Draw(self.img)

    def reducir(self):
        return self.img.resize((self.tam[0] // SS, self.tam[1] // SS), Image.LANCZOS)


def _verrugas(lz, d, rng, zona, n, piel, rojas=0.25, rmin=2.2, rmax=4.6, evitar=()):
    """Verrugas sueltas dentro de una elipse (cx, cy, rx, ry), fuera de las zonas a evitar."""
    cx, cy, rx, ry = zona
    sombra = _oscurecer(piel, 0.72)
    luz = _mezcla(piel, (255, 255, 245), 0.45)
    hechas = 0
    for _ in range(n * 6):
        if hechas >= n:
            break
        a, rr = rng.uniform(0, 2 * math.pi), math.sqrt(rng.random())
        x, y = cx + math.cos(a) * rr * rx, cy + math.sin(a) * rr * ry
        if any(((x - ex) / erx) ** 2 + ((y - ey) / ery) ** 2 < 1 for ex, ey, erx, ery in evitar):
            continue
        r = rng.uniform(rmin, rmax)
        roja = rng.random() < rojas
        color = VERRUGA_ROJA if roja else _mezcla(piel, (150, 140, 100), 0.35)
        lz.punto(x + 0.6, y + 0.9, r + 0.9, sombra, d)
        lz.punto(x, y, r, color, d)
        lz.punto(x - r * 0.35, y - r * 0.35, r * 0.35, luz, d)
        hechas += 1


def _manchas(lz, d, rng, zona, n, color, rmin, rmax, evitar=()):
    cx, cy, rx, ry = zona
    borde = _oscurecer(color, 0.55)
    hechas = 0
    for _ in range(n * 8):
        if hechas >= n:
            break
        a, rr = rng.uniform(0, 2 * math.pi), math.sqrt(rng.random())
        x, y = cx + math.cos(a) * rr * rx, cy + math.sin(a) * rr * ry
        if any(((x - ex) / erx) ** 2 + ((y - ey) / ery) ** 2 < 1 for ex, ey, erx, ery in evitar):
            continue
        lz.poli(_mancha(rng, x, y, rng.uniform(rmin, rmax)), color, borde, 1.6, d)
        hechas += 1


def dibujar(color, boca, ojos_abiertos, escala=1.0, mirando=1, accesorio=None, postura=0, geom_boca=None):
    """Devuelve la rana como RGBA del mismo tamaño que personajes._lienzo(escala)."""
    from .personajes import GEOM_BOCA
    geom_boca = geom_boca or GEOM_BOCA
    f = _FORMA.get(postura, _FORMA[0])
    sx, sy, cab, base = f["sx"], f["sy"], f["cab"], f["base"]
    color = tuple(color)
    piel = _mezcla(color, CREMA, 0.72)
    piel_sombra = _mezcla(piel, (90, 96, 60), 0.3)
    mancha = _mezcla(color, (60, 110, 50), 0.35)
    semilla = sum(c * (i + 7) for i, c in enumerate(color))  # mismas manchas en cada fotograma

    lz = _Lienzo(escala)

    # cuerpo y cabeza (posiciones comunes)
    cuerpo = (180, base - 98 * sy, 124 * sx, 98 * sy)
    cy_cab = 150 + cab
    cabeza = (180, cy_cab, 138, 76)
    ojos = [(112, 92 + cab), (248, 92 + cab)]

    # --- patas traseras: pies en el suelo (sentada) o estiradas (en el aire)
    if not f["salto"]:
        pies = []
        for s in (-1, 1):
            x0 = 180 + s * 112 * sx
            pies.append(_tubo([(x0, SUELO - 10), (x0 + s * 30, SUELO - 4), (x0 + s * 58, SUELO - 2)], [26, 18, 10]))
            for dd in (-1, 0, 1):  # dedos largos y abiertos
                pies.append(_tubo([(x0 + s * 50, SUELO - 3), (x0 + s * (66 + 4 * dd), SUELO - 4 + dd * 5)], [8, 6]))
        lz.grupo(pies, piel_sombra)
        muslos = [_elipse(180 + s * 106 * sx, SUELO - 40 * sy - 4, 58 * sx, 40 * sy, rot=-0.35 * s) for s in (-1, 1)]
    else:
        piernas = []
        for s in (-1, 1):
            cadera = (180 + s * 80, base - 30)
            rodilla = (180 + s * 120, base + 14)
            tobillo = (180 + s * 104, SUELO + 6)
            piernas.append(_tubo([cadera, rodilla], [52, 34]))
            piernas.append(_tubo([rodilla, tobillo, (180 + s * 98, SUELO + 20)], [30, 18, 12]))
            for dd in (-1, 0, 1):
                piernas.append(_tubo([(180 + s * 98, SUELO + 16), (180 + s * (96 + 9 * dd), SUELO + 22)], [8, 6]))
        rng_p = random.Random(semilla + 3)

        def deco_piernas(d):
            for s in (-1, 1):
                for j in range(3):
                    t = (j + 0.5) / 3
                    x = 180 + s * (80 + 40 * t)
                    y = base - 30 + 44 * t
                    lz.poli(_mancha(rng_p, x, y, 9), mancha, _oscurecer(mancha, 0.55), 1.4, d)
        lz.grupo(piernas, piel_sombra, deco_piernas)
        muslos = []

    # --- cuerpo + cabeza, una sola silueta
    rng = random.Random(semilla)
    zona_cab = (cabeza[0], cabeza[1] - 18, cabeza[2] * 0.9, cabeza[3] * 0.62)
    zona_cuerpo = (cuerpo[0], cuerpo[1], cuerpo[2] * 0.95, cuerpo[3] * 0.92)
    tripa = (180, base - 62 * sy, 70 * sx, 58 * sy)
    boca_zona = (180, 178 + cab, 120, 24)

    def deco_cuerpo(d):
        r = random.Random(semilla + 1)
        if not muslos:  # sin muslos aparte (en el aire), sugiere el bulto del costado
            for s in (-1, 1):
                lz.poli(_elipse(180 + s * 112 * sx, cuerpo[1] + 10, 30 * sx, 80 * sy), piel_sombra, None, d=d)
        _manchas(lz, d, r, zona_cuerpo, 13, mancha, 15, 27)
        _manchas(lz, d, r, zona_cab, 8, mancha, 10, 17,
                 evitar=[(x, y, 42, 40) for x, y in ojos] + [boca_zona, (180, ojos[0][1] + 20, 26, 30)])
        _verrugas(lz, d, r, zona_cuerpo, 34, piel)
        _verrugas(lz, d, r, zona_cab, 12, piel, rmin=1.8, rmax=3.4,
                  evitar=[(x, y, 46, 44) for x, y in ojos] + [boca_zona])
        # garganta y barriga claras, con granitos
        lz.poli(_elipse(180, 214 + cab, 82, 22), _mezcla(piel, BARRIGA, 0.7), None, d=d)
        lz.poli(_elipse(*tripa), BARRIGA, BARRIGA_SOMBRA, 1.6, d=d)
        for _ in range(26):
            a, rr = r.uniform(0, 2 * math.pi), math.sqrt(r.random()) * 0.85
            lz.punto(tripa[0] + math.cos(a) * rr * tripa[2], tripa[1] + math.sin(a) * rr * tripa[3],
                     r.uniform(1.0, 1.8), BARRIGA_SOMBRA, d)
        # glándulas parotoides: dos bultos alargados detrás de los ojos
        for s, (ex, ey) in zip((-1, 1), ojos):
            gx, gy = ex + s * 36, ey + 44
            lz.poli(_elipse(gx, gy, 16, 34, rot=0.5 * s), _mezcla(piel, (200, 180, 120), 0.3),
                    _oscurecer(piel, 0.6), 1.6, d)
            for j in range(4):
                lz.punto(gx + s * (j - 1.5) * 3, gy - 18 + j * 11, 1.6, _oscurecer(piel, 0.6), d)

    # los muslos entran en la misma pieza que cuerpo+cabeza: un solo contorno,
    # sin la costura de "globo pegado" que salía al dibujarlos aparte encima
    def deco_muslos(d):
        r = random.Random(semilla + 2)
        for s in (-1, 1):
            mx, my = 180 + s * 106 * sx, SUELO - 40 * sy - 4
            for j in range(3):
                lz.poli(_mancha(r, mx + s * (j - 1) * 30, my + r.uniform(-10, 8), r.uniform(10, 14)),
                        mancha, _oscurecer(mancha, 0.55), 1.4, d)
            _verrugas(lz, d, r, (mx, my, 48 * sx, 32 * sy), 6, piel, rmin=1.8, rmax=3.2)

    def deco_cuerpo_y_muslos(d):
        deco_cuerpo(d)
        if muslos:
            deco_muslos(d)

    lz.grupo([_elipse(*cuerpo), _elipse(*cabeza)] + muslos, piel, deco_cuerpo_y_muslos)

    # --- brazos delanteros, por delante de la barriga
    brazos = []
    for s in (-1, 1):
        hombro = (180 + s * 86 * sx, base - 118 * sy)
        if f["salto"]:
            codo = (180 + s * 96, base - 50)
            mano = (180 + s * 84, base - 6)
        else:
            codo = (180 + s * 106 * sx, base - 60 * sy)
            mano = (180 + s * 92 * sx, SUELO - 6)
        brazos.append(_tubo([hombro, codo, mano], [34, 26, 18]))
        for dd in (-1, 0, 1, 2):
            brazos.append(_tubo([mano, (mano[0] + s * (dd * 9 - 4), mano[1] + 9 - abs(dd) * 2)], [7, 5]))

    def deco_brazos(d):
        r = random.Random(semilla + 4)
        for s in (-1, 1):
            hx, hy = 180 + s * 86 * sx, base - 118 * sy
            for j in range(2):
                lz.poli(_mancha(r, hx + s * (8 + j * 10), hy + 22 + j * 32, 7), mancha,
                        _oscurecer(mancha, 0.55), 1.2, d)
    lz.grupo(brazos, piel, deco_brazos, ancho=2.2)

    # --- sombrero (por detrás de los ojos)
    if accesorio == "sombrero":
        capa = Image.new("RGBA", lz.tam, (0, 0, 0, 0))
        dc = ImageDraw.Draw(capa)
        negro, cinta, luz = (35, 30, 40), (170, 45, 55), (62, 56, 70)
        b = 26 + cab - 6
        lz.poli(_elipse(180, 22 + b, 102, 18), negro, LINEA, 2.2, dc)               # ala
        copa = [(124, 20 + b), (122, -38 + b), (238, -38 + b), (236, 20 + b)]
        lz.poli(copa, negro, LINEA, 2.2, dc)
        lz.poli([(123, 4 + b), (237, 4 + b), (236, 16 + b), (124, 16 + b)], cinta, None, d=dc)
        lz.poli(_elipse(180, -38 + b, 58, 7), luz, LINEA, 2.0, dc)
        lz.linea([(134, -28 + b), (134, 0 + b)], luz, 3, dc)
        capa = capa.rotate(-8 * mirando, resample=Image.BICUBIC, center=lz.p(180, 22 + b))
        lz.img.alpha_composite(capa)
        lz.d = ImageDraw.Draw(lz.img)

    # --- ojos: cúpulas salientes, iris dorado con pupila horizontal
    dx = 8 * mirando
    for ex, ey in ojos:
        lz.poli(_elipse(ex, ey, 46, 43), piel, LINEA, 2.6)
        lz.poli(_elipse(ex, ey + 4, 33, 30), (250, 248, 236), LINEA, 1.6)
        if ojos_abiertos:
            ix = ex + dx
            lz.poli(_elipse(ix, ey + 5, 25, 24), IRIS, IRIS_OSCURO, 1.6)
            r = random.Random(ex)
            for _ in range(10):  # retícula oscura del iris
                a = r.uniform(0, 2 * math.pi)
                lz.punto(ix + math.cos(a) * r.uniform(9, 20), ey + 5 + math.sin(a) * r.uniform(9, 20),
                         r.uniform(1.0, 1.8), IRIS_OSCURO)
            lz.poli(_elipse(ix, ey + 6, 14, 7), PUPILA, None)
            lz.punto(ix - 9, ey - 4, 4.5, (255, 255, 255))
            # párpado superior, algo caído (mirada de sapo tranquilo)
            lz.poli(_curva((ex - 36, ey - 2), (ex, ey - 46), (ex + 36, ey - 2)) +
                    _curva((ex + 36, ey - 2), (ex, ey - 16), (ex - 36, ey - 2))[1:-1], piel, None)
            lz.linea(_curva((ex - 34, ey - 3), (ex, ey - 17), (ex + 34, ey - 3)), LINEA, 2.4)
        else:
            lz.poli(_elipse(ex, ey + 4, 34, 31), piel, None)
            lz.linea(_curva((ex - 30, ey + 6), (ex, ey + 20), (ex + 30, ey + 6)), LINEA, 3.2)
            for j in (-1, 0, 1):  # pestañas cortas
                bx = ex + j * 14
                lz.linea([(bx, ey + 12 + (1 - abs(j)) * 3), (bx + j * 3, ey + 20 + (1 - abs(j)) * 4)], LINEA, 2)
        lz.linea(_curva((ex - 40, ey - 18), (ex, ey - 46), (ex + 40, ey - 18)), _oscurecer(piel, 0.75), 2)

    # --- gafas redondas con cristal tintado
    if accesorio == "gafas":
        capa = Image.new("RGBA", lz.tam, (0, 0, 0, 0))
        dc = ImageDraw.Draw(capa)
        montura = (45, 35, 30, 255)
        for ex, ey in ojos:
            lz.poli(_elipse(ex, ey + 2, 40, 40), (170, 210, 235, 70), montura, 4, dc)
            lz.poli(_elipse(ex - 18, ey - 18, 7, 5, rot=-0.6), (255, 255, 255, 150), None, d=dc)
        lz.linea([(152, 90 + cab), (180, 82 + cab), (208, 90 + cab)], montura, 4, dc)
        lz.linea([(72, 90 + cab), (54, 102 + cab)], montura, 3.5, dc)
        lz.linea([(288, 90 + cab), (306, 102 + cab)], montura, 3.5, dc)
        lz.img.alpha_composite(capa)
        lz.d = ImageDraw.Draw(lz.img)

    # --- orificios nasales
    for nx in (166, 194):
        lz.punto(nx, 130 + cab, 2.8, LINEA)

    # --- boca: las comisuras son siempre las mismas del reposo y la boca se abre
    # desde ellas (labio superior casi recto, mandíbula curva), sin dejar
    # sobrar la línea de la sonrisa a los lados
    yb = 170 + cab
    izq, der = (74, yb - 6), (286, yb - 6)

    def comisuras(a, b):
        lz.linea(_curva((a[0] - 8, a[1] - 8), (a[0] - 4, a[1] + 2), (a[0] + 6, a[1] + 2)), LINEA, 2.6)
        lz.linea(_curva((b[0] + 8, b[1] - 8), (b[0] + 4, b[1] + 2), (b[0] - 6, b[1] + 2)), LINEA, 2.6)

    if boca == 0:
        lz.linea(_curva(izq, (180, yb + 26), der), LINEA, 3.4)
        comisuras(izq, der)
    else:
        if boca == 5:  # oclusiva: labios apretados, apenas una rendija
            a, b, alto = (78, yb - 4), (282, yb - 4), 8
        else:
            x0, x1, alto = geom_boca[boca]
            # las vocales redondas recogen las comisuras, las anchas las estiran
            a = (74 + (x0 - 74) * 0.6, yb - 3)
            b = (286 + (x1 - 286) * 0.6, yb - 3)
        cx = (a[0] + b[0]) / 2
        sup = _curva(a, (cx, yb - 1), b)
        inf = _curva(b, (cx, yb - 4 + 2 * alto), a)
        boca_pts = sup + inf[1:-1]
        lz.poli(boca_pts, BOCA_DENTRO, LINEA, 2.8)
        if boca != 5:
            capa = Image.new("RGBA", lz.tam, (0, 0, 0, 0))
            lz.poli(_elipse(cx, yb + alto * 0.8, min((b[0] - a[0]) * 0.22, 40), alto * 0.3), LENGUA, None,
                    d=ImageDraw.Draw(capa))
            mascara = Image.new("L", lz.tam, 0)
            ImageDraw.Draw(mascara).polygon(lz.q(boca_pts), fill=255)
            capa.putalpha(ImageChops.multiply(capa.getchannel("A"), mascara))
            lz.img.alpha_composite(capa)
            lz.d = ImageDraw.Draw(lz.img)
        lz.linea(sup, LINEA, 3)
        comisuras(a, b)
    return lz.reducir()


if __name__ == "__main__":
    # hoja de prueba: posturas, bocas y miradas de las dos ranas
    hoja = Image.new("RGBA", (360 * 8, 480 * 3), (120, 170, 190, 255))
    for fila, (col, acc) in enumerate((((95, 170, 80), "sombrero"), ((150, 185, 60), "gafas"))):
        for j, pz in enumerate(POSTURAS):
            hoja.alpha_composite(dibujar(col, 0, True, 1.0, 1 - j % 3, acc, pz), (360 * j, 480 * fila))
        for j, b in enumerate((1, 3, 5, 6)):
            hoja.alpha_composite(dibujar(col, b, j != 2, 1.0, 0, acc), (360 * (4 + j), 480 * fila))
    for j, b in enumerate((0, 2, 4)):
        hoja.alpha_composite(dibujar((95, 170, 80), b, True, 1.0, 1, None, j), (360 * j, 960))
    hoja.convert("RGB").resize((hoja.width // 2, hoja.height // 2), Image.LANCZOS).save("ranas_preview.png")
    print("ranas_preview.png guardado")
