"""
Eventos extra (salen al azar y también se pueden lanzar desde MIDI):

    cerdo_asoma   el porc negre saca la cabeza por abajo, husmea y vuelve a bajar
    grillo        un grillo cruza a saltos por delante
    rana_guapa    una rana con pintalabios y pestañas sube del estanque y guiña un ojo
    pedo          una de las dos ranas (al azar) se tira un pedo; da un bote y cierra los ojos
    muchedumbre   público aplaudiendo que asoma por abajo
    asnos         dos burros asoman por los lados y se ríen
    motocultor    un pagès con motocultor por el camí, echando muchísimo humo
    bombilla      una bombilla baja del techo, se enciende y vuelve a subir
    cabra         un payès toca el tamborí (redoble); una cabra entra, le da una coz y se esconde

Los que "asoman" (cerdo_asoma, rana_guapa, muchedumbre, asnos, bombilla, cabra) se
quedan mientras dure la nota MIDI. La velocidad de la nota cambia el tamaño o la
intensidad.

El pedo usa dos interfaces opcionales que ranas.py aplica si existen:
  afecta_rana(t) -> {indice_rana: {"bote": n, "ojos": bool}}   la rana da un bote y cierra los ojos
  viento(t)      -> {"izq" | "der": px}                         dobla las cañas de ese lado
Si ranas.py no las usa, el pedo se ve igual, pero sin esas reacciones.

Se registran solos en eventos.TIPOS al importar este módulo, así que basta con
`import eventos_extra` en ranas.py.
"""

import math
import random

from PIL import Image, ImageDraw, ImageFont

from .escena import X_RANAS, Y_CAMI, Y_FRENTE
from . import sprite_cabra as _sprite_cabra
from . import sprite_campo as _sprite_campo
from . import sprite_payes_tambor as _sprite_payes
from .eventos import SS, TIPOS, Evento, EventoDeCruce, _marcos, _reducir


def dibujar_cabeza_cerdo(k, ojos_abiertos=True, hocico=0.0, orejas=0.0):
    """Cabeza de porc negre vista de frente, para asomar desde abajo.
    hocico -1..1 mueve el morro de lado (husmea), orejas 0..1 las levanta."""
    w, h = int(240 * k), int(230 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    negro, gris, rosa, rosa_osc = (38, 34, 38), (72, 66, 72), (176, 120, 132), (110, 66, 80)

    def E(x0, y0, x1, y1, **kw):
        d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    def P(pts, **kw):
        d.polygon([(x * k, y * k) for x, y in pts], **kw)

    lev = 14 * orejas
    P([(40, 70), (62, 6 - lev), (98, 52)], fill=negro)        # oreja izq.
    P([(200, 70), (178, 6 - lev), (142, 52)], fill=negro)     # oreja der.
    P([(56, 54), (64, 22 - lev), (86, 50)], fill=gris)
    P([(184, 54), (176, 22 - lev), (154, 50)], fill=gris)
    E(20, 40, 220, 230, fill=negro)                            # cabeza (sigue fuera de cuadro)
    E(52, 58, 150, 120, fill=gris)                             # brillo
    for cx in (85, 155):                                       # ojos
        if ojos_abiertos:
            E(cx - 17, 92, cx + 17, 126, fill=(250, 250, 250))
            E(cx - 8 + hocico * 4, 101, cx + 8 + hocico * 4, 119, fill=(12, 12, 12))
            E(cx - 5 + hocico * 4, 103, cx + 1 + hocico * 4, 109, fill=(255, 255, 255))
        else:
            d.line([((cx - 15) * k, 110 * k), ((cx + 15) * k, 110 * k)], fill=(200, 200, 200),
                   width=max(2, int(4 * k)))
    dx = 10 * hocico
    E(72 + dx, 132, 168 + dx, 196, fill=rosa, outline=rosa_osc, width=max(1, int(3 * k)))  # morro
    E(96 + dx, 152, 112 + dx, 176, fill=rosa_osc)
    E(128 + dx, 152, 144 + dx, 176, fill=rosa_osc)
    d.arc([92 * k, 186 * k, 148 * k, 214 * k], 20, 160, fill=(20, 18, 20), width=max(2, int(4 * k)))
    return img


def dibujar_grillo(k, patas=0.0):
    """Grillo verde de perfil, mirando a la derecha. patas 0 (recogidas) .. 1 (estiradas, saltando)."""
    w, h = int(150 * k), int(90 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    verde, osc, claro = (96, 150, 52), (60, 100, 34), (150, 196, 90)

    def L(pts, ancho, c=osc):
        d.line([(x * k, y * k) for x, y in pts], fill=c, width=max(1, int(ancho * k)), joint="curve")

    # antenas
    L([(118, 46), (132, 18), (146, 6)], 2)
    L([(116, 46), (122, 14), (128, 2)], 2)
    # pata trasera (la del salto)
    rod = (50 - 12 * patas, 30 + 10 * patas)
    pie = (30 - 22 * patas, 78 + 6 * patas)
    L([(70, 56), rod, pie], 6, verde)
    L([rod, pie], 3)
    # patas delanteras
    L([(96, 62), (100, 76), (108, 80)], 3)
    L([(84, 62), (82, 78), (76, 82)], 3)
    # cuerpo y alas
    d.ellipse([40 * k, 40 * k, 112 * k, 70 * k], fill=verde, outline=osc, width=max(1, int(2 * k)))
    d.polygon([(46 * k, 46 * k), (100 * k, 42 * k), (36 * k, 60 * k)], fill=claro)
    # cabeza
    d.ellipse([100 * k, 36 * k, 132 * k, 64 * k], fill=verde, outline=osc, width=max(1, int(2 * k)))
    d.ellipse([114 * k, 40 * k, 126 * k, 52 * k], fill=(255, 255, 255))
    d.ellipse([118 * k, 43 * k, 125 * k, 50 * k], fill=(15, 15, 15))
    return img


class CerdoAsoma(Evento):
    """El cerdo saca la cabeza por el borde inferior, husmea y vuelve a bajar.
    Lanzado desde MIDI, se queda arriba mientras dure la nota."""
    capa = "frente"
    SUBIR, BAJAR, MIN_ARRIBA = 0.35, 0.3, 0.8
    AJUSTA_CENIT = True  # por MIDI, la nota marca cuando husmea arriba, no cuando empieza a subir

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        self.velocidad = 100
        self.mantener = int(2.0 * fps)
        self.cx = rng.choice((0.5, 0.12, 0.88, 0.38, 0.62)) * W
        self.rng = random.Random(rng.random())
        self._preparar()

    def _preparar(self):
        fps = self.fps
        tam = SS * (0.85 + 0.45 * self.velocidad / 127) * self.escala
        self.frames = {}
        for ojos in (True, False):
            for h in (-1, 0, 1):
                for o in (0, 1):
                    self.frames[(ojos, h, o)] = _reducir(dibujar_cabeza_cerdo(tam, ojos, h, o))
        self.alto = self.frames[(True, 0, 0)].height
        self.n_sub = max(2, int(self.SUBIR * fps))
        self.n_baj = max(2, int(self.BAJAR * fps))
        self.n_arriba = max(int(self.MIN_ARRIBA * fps), self.mantener)
        self.duracion = self.n_sub + self.n_arriba + self.n_baj
        # parpadeos durante el tiempo arriba
        self.parpadeos = set()
        t = int(self.rng.uniform(0.4, 1.2) * fps)
        while t < self.n_arriba:
            self.parpadeos.update(range(t, t + max(2, int(0.12 * fps))))
            t += int(self.rng.uniform(1.2, 2.5) * fps)

    def ajustar_a_nota(self):
        self._preparar()

    def sprites(self, t):
        visible = 0.95  # parte de la cabeza que asoma
        if t < self.n_sub:  # sube con un pequeño rebote
            p = t / self.n_sub
            sub = 1 - (1 - p) ** 3 + 0.08 * math.sin(math.pi * p)
        elif t < self.n_sub + self.n_arriba:
            sub = 1.0 + 0.015 * math.sin(t * 0.5)
        else:
            p = (t - self.n_sub - self.n_arriba) / self.n_baj
            sub = 1 - p * p
        ta = t - self.n_sub
        arriba = 0 <= ta < self.n_arriba
        husmea = int(round(math.sin(ta * 0.35))) if arriba else 0
        ojos = not (arriba and ta in self.parpadeos)
        orejas = 1 if t < self.n_sub + 3 else 0  # orejas tiesas al salir
        im = self.frames[(ojos, husmea, orejas)]
        y = int(self.H - self.alto * visible * max(0.0, sub))
        return [(im, int(self.cx - im.width / 2), y)]

    def x_interes(self, t):
        return self.cx


class Grillo(EventoDeCruce):
    """Un grillo cruza por delante a saltos. Por MIDI: entra, salta quieto en un sitio
    y se va dando media vuelta por donde ha venido al soltar la nota."""
    capa = "frente"
    SEG = 7
    SEG_ENTRA, SEG_SALE = 1.0, 1.0

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        self.velocidad = 100
        esp = self.dir == -1
        k = SS * 0.85 * self.escala
        self.quieto = _reducir(dibujar_grillo(k, 0.0), esp)
        self.saltando = _reducir(dibujar_grillo(k, 1.0), esp)
        self.quieto_vuelta = self.quieto.transpose(Image.FLIP_LEFT_RIGHT)
        self.saltando_vuelta = self.saltando.transpose(Image.FLIP_LEFT_RIGHT)
        self.ancho = self.quieto.width
        self.duracion = int(self.SEG * fps)
        self.n_saltos = rng.randint(6, 9)

    def _estado(self, t):
        x = self.x_lineal(t, self.ancho, self.SEG)
        # mismo ritmo de saltos de siempre (n_saltos a lo largo de SEG segundos),
        # calculado por tiempo en vez de fracción del total para que no cambie
        # si la duración real varía por venir de una nota MIDI
        fase = (t / self.fps * self.n_saltos / self.SEG) % 1.0
        vuelo = 0.55  # parte de cada ciclo en el aire
        altura = (0.08 + 0.1 * self.velocidad / 127) * self.H
        if fase < vuelo:
            q = fase / vuelo
            return x, 4 * q * (1 - q) * altura, True
        return x, 0.0, False

    def sprites(self, t):
        x, alto, en_aire = self._estado(t)
        if self._saliendo:
            im = self.saltando_vuelta if en_aire else self.quieto_vuelta
        else:
            im = self.saltando if en_aire else self.quieto
        y = int(Y_FRENTE * self.H) - im.height - int(alto)
        return [(im, int(x), y)]

    def x_interes(self, t):
        return self._estado(t)[0] + self.ancho / 2



# ============================================================================
# Utilidades comunes
# ============================================================================

def _fuente(tam):
    for nombre in ("arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(nombre, tam)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=tam)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def _texto(txt, tam, color, borde=(255, 255, 255), angulo=0):
    """Texto tipo cómic con borde, como imagen RGBA."""
    f = _fuente(tam)
    caja = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), txt, font=f, stroke_width=max(2, tam // 8))
    w, h = caja[2] - caja[0] + 8, caja[3] - caja[1] + 8
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((4 - caja[0], 4 - caja[1]), txt, font=f, fill=color,
                             stroke_width=max(2, tam // 8), stroke_fill=borde)
    return img.rotate(angulo, expand=True, resample=Image.BICUBIC) if angulo else img


def _curva_asoma(t, n_sub, n_arriba, n_baj, rebote=0.08):
    """0 = escondido, 1 = fuera. Sube con rebote, se mantiene y baja."""
    if t < n_sub:
        p = t / n_sub
        return 1 - (1 - p) ** 3 + rebote * math.sin(math.pi * p)
    if t < n_sub + n_arriba:
        return 1.0
    p = min(1.0, (t - n_sub - n_arriba) / n_baj)
    return 1 - p * p


class Asoma(Evento):
    """Base para eventos que aparecen, se quedan lo que dure la nota y se van."""
    capa = "frente"
    SUBIR, BAJAR, MIN_ARRIBA, POR_DEFECTO = 0.4, 0.35, 1.0, 2.5

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        self.velocidad = 100
        self.mantener = int(self.POR_DEFECTO * fps)
        self.rng = random.Random(rng.random())
        self._preparar()

    def ajustar_a_nota(self):
        self._preparar()

    def _preparar(self):
        self.n_sub = max(2, int(self.SUBIR * self.fps))
        self.n_baj = max(2, int(self.BAJAR * self.fps))
        self.n_arriba = max(int(self.MIN_ARRIBA * self.fps), self.mantener)
        self.duracion = self.n_sub + self.n_arriba + self.n_baj
        self.dibujar()

    def dibujar(self):
        pass

    def fuera(self, t):
        return _curva_asoma(t, self.n_sub, self.n_arriba, self.n_baj)

    def t_arriba(self, t):
        """Fotogramas desde que terminó de salir (negativo mientras sube)."""
        return t - self.n_sub


# ============================================================================
# Rana guapa: pintalabios, pestañas y guiño
# ============================================================================

def dibujar_rana_guapa(k, guino=False, beso=False):
    w, h = int(300 * k), int(330 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base, osc, barriga = (120, 196, 110), (78, 150, 72), (200, 236, 170)

    def E(x0, y0, x1, y1, **kw):
        d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    ancho = max(1, int(4 * k))
    E(30, 150, 270, 340, fill=base, outline=osc, width=ancho)        # cuerpo (sigue bajo el agua)
    E(80, 210, 220, 340, fill=barriga)
    E(25, 95, 275, 245, fill=base, outline=osc, width=ancho)         # cabeza
    # lazo rosa
    rosa, rosa_osc = (240, 110, 160), (200, 70, 120)
    d.polygon([(150 * k, 92 * k), (108 * k, 66 * k), (112 * k, 112 * k)], fill=rosa, outline=rosa_osc)
    d.polygon([(150 * k, 92 * k), (192 * k, 66 * k), (188 * k, 112 * k)], fill=rosa, outline=rosa_osc)
    E(138, 80, 162, 104, fill=rosa_osc)
    # ojos
    for i, cx in enumerate((90, 210)):
        E(cx - 44, 48, cx + 44, 138, fill=base, outline=osc, width=ancho)
        cerrado = guino and i == 1
        if cerrado:
            d.arc([(cx - 28) * k, 78 * k, (cx + 28) * k, 112 * k], 200, 340, fill=(30, 40, 30), width=max(2, int(6 * k)))
            pest_y, pest_base = 92, 1
        else:
            E(cx - 30, 62, cx + 30, 122, fill=(255, 255, 255))
            E(cx - 15, 76, cx + 15, 110, fill=(30, 22, 40))
            E(cx - 8, 80, cx, 90, fill=(255, 255, 255))
            d.arc([(cx - 32) * k, 58 * k, (cx + 32) * k, 124 * k], 200, 340, fill=(160, 110, 200), width=max(2, int(7 * k)))  # sombra
            pest_y, pest_base = 62, 0
        for j, a in enumerate((-60, -30, 0, 30, 60)):  # pestañas
            ra = math.radians(a - 90)
            x0, y0 = cx + math.cos(ra) * 26, pest_y + 18 + math.sin(ra) * 22 * (0.4 if pest_base else 1)
            x1, y1 = cx + math.cos(ra) * 42, pest_y + 18 + math.sin(ra) * 38 * (0.5 if pest_base else 1) - 4
            d.line([(x0 * k, y0 * k), (x1 * k, y1 * k)], fill=(20, 15, 25), width=max(2, int(5 * k)))
    # colorete
    E(48, 170, 92, 194, fill=(250, 150, 170))
    E(208, 170, 252, 194, fill=(250, 150, 170))
    # labios con pintalabios
    rojo, rojo_osc = (215, 30, 60), (150, 10, 40)
    if beso:
        E(128, 172, 172, 214, fill=rojo, outline=rojo_osc, width=ancho)
        E(142, 186, 158, 200, fill=rojo_osc)
    else:
        E(108, 178, 192, 206, fill=rojo, outline=rojo_osc, width=ancho)
        d.line([(112 * k, 192 * k), (150 * k, 196 * k), (188 * k, 192 * k)], fill=rojo_osc, width=max(1, int(3 * k)))
        E(120, 180, 140, 188, fill=(250, 120, 140))
    return img


def dibujar_corazon(k, color=(235, 40, 80)):
    s = int(60 * k)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, s * 0.55, s * 0.55], fill=color)
    d.ellipse([s * 0.45, 0, s, s * 0.55], fill=color)
    d.polygon([(s * 0.04, s * 0.38), (s * 0.96, s * 0.38), (s * 0.5, s * 0.95)], fill=color)
    return img


class RanaGuapa(Asoma):
    """Sube del estanque entre las dos ranas, guiña un ojo, lanza un beso y se hunde."""
    SUBIR, BAJAR, MIN_ARRIBA, POR_DEFECTO = 0.6, 0.5, 1.8, 3.0

    def dibujar(self):
        k = SS * (0.65 + 0.3 * self.velocidad / 127) * self.escala
        self.normal = _reducir(dibujar_rana_guapa(k))
        self.guino = _reducir(dibujar_rana_guapa(k, guino=True))
        self.beso = _reducir(dibujar_rana_guapa(k, guino=True, beso=True))
        self.corazon = [_reducir(dibujar_corazon(SS * self.escala * e)) for e in (0.5, 0.7, 0.9)]
        self.cx = self.W * 0.5
        self.alto = self.normal.height
        n = self.n_arriba
        self.t_guino = (int(n * 0.25), int(n * 0.25) + max(6, int(0.45 * self.fps)))
        self.t_beso = (int(n * 0.55), int(n * 0.55) + max(8, int(0.6 * self.fps)))

    def sprites(self, t):
        ta = self.t_arriba(t)
        im = self.normal
        if self.t_guino[0] <= ta < self.t_guino[1]:
            im = self.guino
        elif self.t_beso[0] <= ta < self.t_beso[1]:
            im = self.beso
        y = int(self.H * 1.02 - self.alto * 0.88 * self.fuera(t))  # el cuerpo se queda dentro del agua
        x = int(self.cx - im.width / 2 + math.sin(t * 0.15) * 3 * self.escala)
        out = [(im, x, y)]
        if ta >= self.t_beso[0]:  # corazones que suben tras el beso
            for j in range(3):
                tj = ta - self.t_beso[0] - j * 6
                if 0 <= tj < 30:
                    c = self.corazon[min(2, tj // 10)]
                    out.append((c, int(self.cx + (j - 1) * 30 * self.escala + math.sin(tj * 0.3) * 8),
                                int(y - tj * 4 * self.escala)))
        return out

    def x_interes(self, t):
        return self.cx


# ============================================================================
# Pedo
# ============================================================================

class Pedo(Evento):
    """Una de las dos ranas, al azar, se tira un pedo: le sale humo por detrás."""
    capa = "frente"
    SEG = 4.0
    CHORRO = 0.6   # segundos que dura la salida de gas
    VIDA = 2.4     # segundos que tarda en disiparse cada bocanada

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        self.velocidad = 100
        self.rana = rng.choice((0, 1))
        self.duracion = int(self.SEG * fps)
        self.rng = random.Random(rng.random())
        self.lado = -1 if self.rana == 0 else 1  # el humo sale hacia fuera de la pantalla
        # punto de salida: la parte trasera-baja de la rana, junto a la pata de atrás
        self.x0 = X_RANAS[self.rana] * W + self.lado * 0.062 * W
        self.y0 = 0.815 * H
        # bocanadas en 10 tamaños x 5 niveles de transparencia, precalculadas
        self.nube = []
        for i in range(10):
            base = self._bocanada(SS * self.escala * (0.5 + i * 0.32))
            niveles = []
            for nivel in range(5):
                im = _reducir(base)
                f = (5 - nivel) / 5
                im.putalpha(im.getchannel("A").point(lambda a, f=f: int(a * f)))
                niveles.append(im)
            self.nube.append(niveles)
        # partículas: (nacimiento s, ángulo, alcance, subida, crecimiento)
        n = 16
        self.particulas = []
        for j in range(n):
            nace = self.CHORRO * j / n + self.rng.uniform(0, 0.03)
            ang = math.radians(self.rng.uniform(-25, 30))       # hacia fuera, un poco abajo/arriba
            alcance = self.rng.uniform(0.07, 0.15) * W * (1.3 - 0.5 * j / n)  # las primeras salen con más fuerza
            subida = self.rng.uniform(0.02, 0.06) * H
            self.particulas.append((nace, ang, alcance, subida, self.rng.uniform(0.8, 1.2)))
        ang_txt = -12 * self.lado
        self.prrt = _texto(rng.choice(("PRRRT!", "PFFFF!", "PRRT!", "BRRRP!")), int(30 * self.escala),
                           (120, 90, 30), angulo=ang_txt)

    @staticmethod
    def _bocanada(k):
        s = int(70 * k) + 2
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for (x, y, r, c) in ((0.5, 0.56, 0.32, (140, 160, 72, 215)), (0.32, 0.5, 0.22, (170, 184, 90, 205)),
                             (0.68, 0.48, 0.24, (160, 176, 82, 205)), (0.5, 0.33, 0.22, (186, 196, 104, 195))):
            d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=c)
        return img

    def sprites(self, t):
        seg = t / self.fps
        out = []
        for nace, ang, alcance, subida, crece in self.particulas:
            edad = seg - nace
            if edad < 0 or edad > self.VIDA:
                continue
            q = edad / self.VIDA
            dist = alcance * (1 - math.exp(-edad * 4))          # sale disparada y frena
            x = self.x0 + self.lado * dist * math.cos(ang)
            y = self.y0 - dist * math.sin(ang) * 0.5 - subida * q  # y sube despacio
            tam = min(9, int((0.15 + q * 1.1) * 9 * crece))
            nivel = min(4, int(max(0.0, q - 0.35) / 0.65 * 5))   # se desvanece en la segunda mitad
            im = self.nube[tam][nivel]
            out.append((im, int(x - im.width / 2), int(y - im.height / 2)))
        if 0.0 < seg < 1.6:  # onomatopeya
            out.append((self.prrt, int(self.x0 + self.lado * 0.06 * self.W - self.prrt.width / 2),
                        int(self.y0 - 0.2 * self.H)))
        if 0.8 < seg < 3.4:  # líneas de peste
            ln = Image.new("RGBA", (int(60 * self.escala), int(70 * self.escala)), (0, 0, 0, 0))
            dl = ImageDraw.Draw(ln)
            for j in range(3):
                pts = [(10 + j * 18 + 5 * math.sin((yy + t * 3) * 0.25), yy) for yy in range(0, 60, 4)]
                dl.line([(x * self.escala, y * self.escala) for x, y in pts], fill=(120, 150, 50, 200),
                        width=max(2, int(3 * self.escala)))
            out.append((ln, int(self.x0 + self.lado * 0.08 * self.W - ln.width / 2), int(self.y0 - 0.17 * self.H)))
        return out

    def viento(self, t):
        """Ráfaga que dobla las cañas del lado de la rana: se doblan hacia fuera y
        vuelven oscilando. Devuelve {"izq" | "der": desplazamiento de la punta en px}."""
        seg = t / self.fps
        if seg < 0.05:
            return {}
        a = 0.055 * self.W * (0.6 + 0.6 * self.velocidad / 127)
        s = seg - 0.05
        px = a * math.sin(2 * math.pi * s / 1.1) * math.exp(-s / 0.75)
        return {("izq" if self.lado == -1 else "der"): self.lado * px}

    def afecta_rana(self, t):
        """La rana da un bote al soltarlo y cierra los ojos un momento."""
        p = t / self.fps
        bote = int(max(0.0, math.sin(min(1.0, p / 0.35) * math.pi)) * 6) if p < 0.35 else 0
        return {self.rana: {"bote": bote, "ojos": not (0.0 <= p < 1.2)}}

    def x_interes(self, t):
        return self.x0  # la otra rana mira (y la que se lo tira mira hacia su pedo)


# ============================================================================
# Muchedumbre aplaudiendo
# ============================================================================

class Muchedumbre(Asoma):
    """Público que asoma por abajo y aplaude."""
    SUBIR, BAJAR, MIN_ARRIBA, POR_DEFECTO = 0.5, 0.5, 1.5, 3.0

    def dibujar(self):
        W, H = self.W, self.H
        self.alto = int(H * (0.2 + 0.08 * self.velocidad / 127))
        rng = random.Random(7)
        pieles = [(240, 200, 170), (220, 170, 130), (190, 140, 100), (150, 100, 70), (250, 215, 190)]
        ropas = [(60, 80, 140), (150, 50, 50), (60, 120, 80), (200, 160, 50), (90, 60, 120), (40, 40, 50),
                 (180, 90, 40)]
        pelos = [(40, 30, 25), (90, 60, 30), (200, 170, 90), (20, 20, 20), (150, 150, 150), (130, 50, 30)]
        filas = []
        for fila, (esc, y_base) in enumerate(((0.8, 0.55), (1.0, 1.0))):
            r = H * 0.045 * esc
            x = rng.uniform(0, r)
            while x < W + r:
                filas.append((fila, x, y_base, r, rng.choice(pieles), rng.choice(ropas), rng.choice(pelos),
                              rng.random() < 0.5))
                x += r * rng.uniform(2.0, 2.6)
        self.frames = []
        for paso in range(2):  # manos separadas / juntas
            img = Image.new("RGBA", (W * SS, self.alto * SS), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            for fila, x, y_base, r, piel, ropa, pelo, alterno in filas:
                x, r = x * SS, r * SS
                yb = y_base * self.alto * SS
                cabeza_y = yb - r * 2.6
                d.ellipse([x - r * 1.6, yb - r * 1.4, x + r * 1.6, yb + r * 2], fill=ropa)  # hombros
                d.ellipse([x - r, cabeza_y - r, x + r, cabeza_y + r], fill=piel)
                d.chord([x - r * 1.05, cabeza_y - r * 1.1, x + r * 1.05, cabeza_y + r * 0.6], 180, 360, fill=pelo)
                d.ellipse([x - r * 0.45, cabeza_y - r * 0.05, x - r * 0.25, cabeza_y + r * 0.2], fill=(20, 20, 20))
                d.ellipse([x + r * 0.25, cabeza_y - r * 0.05, x + r * 0.45, cabeza_y + r * 0.2], fill=(20, 20, 20))
                d.chord([x - r * 0.45, cabeza_y + r * 0.2, x + r * 0.45, cabeza_y + r * 0.75], 0, 180, fill=(120, 30, 30))
                juntas = (paso == 0) != alterno
                sep = r * (0.25 if juntas else 1.0)
                manos_y = cabeza_y + r * 1.8
                for lado in (-1, 1):
                    hx = x + lado * sep
                    d.line([(x + lado * r * 1.2, yb - r * 0.6), (hx, manos_y)], fill=ropa, width=int(r * 0.55))
                    d.ellipse([hx - r * 0.32, manos_y - r * 0.4, hx + r * 0.32, manos_y + r * 0.4], fill=piel)
                if juntas:  # marquitas de "clap"
                    for a in (-50, -90, -130):
                        ra = math.radians(a)
                        d.line([(x + math.cos(ra) * r * 0.6, manos_y + math.sin(ra) * r * 0.6),
                                (x + math.cos(ra) * r * 1.0, manos_y + math.sin(ra) * r * 1.0)],
                               fill=(255, 240, 120), width=max(2, int(r * 0.12)))
            self.frames.append(_reducir(img))

    def sprites(self, t):
        im = self.frames[(t // max(1, int(self.fps / 8))) % 2]  # 4 aplausos por segundo
        bote = int(abs(math.sin(t * 0.8)) * 3 * self.escala)
        y = int(self.H - self.alto * self.fuera(t)) + bote
        return [(im, 0, y)]

    def x_interes(self, t):
        return self.W / 2


# ============================================================================
# Asnos que asoman y se ríen
# ============================================================================

def dibujar_cabeza_asno(k, boca=0.0, orejas=0.0):
    """Cabeza de burro de perfil mirando a la derecha. boca 0..1 (abierta, riendo)."""
    w, h = int(280 * k), int(260 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gris, osc, claro, crin = (110, 100, 96), (70, 64, 62), (196, 186, 176), (50, 44, 42)

    def E(x0, y0, x1, y1, **kw):
        d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    def P(pts, **kw):
        d.polygon([(x * k, y * k) for x, y in pts], **kw)

    caida = 25 * orejas
    P([(70, 70), (40 - caida, 0 + caida), (90, 58)], fill=gris, outline=osc)       # orejas
    P([(100, 64), (95 - caida * 0.5, 2 + caida), (122, 60)], fill=gris, outline=osc)
    P([(66, 62), (50 - caida, 16 + caida), (82, 58)], fill=(200, 160, 160))
    P([(0, 260), (40, 90), (110, 70), (120, 260)], fill=gris)                      # cuello
    P([(30, 100), (60, 66), (80, 80), (40, 130)], fill=crin)                        # crin
    E(40, 60, 170, 170, fill=gris)                                                  # cráneo
    P([(120, 80), (240, 110 - 10 * boca), (250, 150), (130, 170)], fill=gris)       # hocico superior
    E(196, 100 - 10 * boca, 262, 156 - 6 * boca, fill=claro)                        # morro
    E(236, 114 - 10 * boca, 248, 126 - 10 * boca, fill=osc)                         # orificio nasal
    # mandíbula: se abre girando hacia abajo
    ab = 50 * boca
    P([(130, 160), (240, 150 + ab * 0.2), (246, 168 + ab), (140, 180)], fill=gris)
    E(200, 146 + ab * 0.6, 252, 178 + ab, fill=claro)
    if boca > 0.2:
        P([(150, 162), (244, 152), (244, 160 + ab * 0.85), (150, 172)], fill=(120, 40, 50))  # boca por dentro
        for i in range(5):  # dientes grandotes
            x = 190 + i * 11
            d.rectangle([x * k, 148 * k, (x + 9) * k, 164 * k], fill=(250, 246, 220), outline=(180, 170, 140))
        d.ellipse([200 * k, (166 + ab * 0.5) * k, 236 * k, (180 + ab * 0.7) * k], fill=(220, 110, 130))  # lengua
    # ojo (cerrado de risa si abre mucho la boca)
    if boca > 0.5:
        d.arc([96 * k, 88 * k, 126 * k, 112 * k], 200, 340, fill=(20, 20, 20), width=max(2, int(5 * k)))
    else:
        E(98, 84, 124, 110, fill=(250, 250, 250))
        E(106, 88, 122, 106, fill=(20, 20, 20))
    return img


class Asnos(Asoma):
    """Dos burros asoman por los lados de la pantalla y se ríen."""
    SUBIR, BAJAR, MIN_ARRIBA, POR_DEFECTO = 0.5, 0.45, 2.0, 3.0

    def dibujar(self):
        k = SS * (0.65 + 0.3 * self.velocidad / 127) * self.escala
        self.frames = {}
        for b in range(4):
            for o in (0, 1):
                im = _reducir(dibujar_cabeza_asno(k, b / 3, o))
                self.frames[(b, o, 1)] = im
                self.frames[(b, o, -1)] = im.transpose(Image.FLIP_LEFT_RIGHT)
        self.ancho = self.frames[(0, 0, 1)].width
        self.alto = self.frames[(0, 0, 1)].height
        tam = int(34 * self.escala * (0.8 + 0.4 * self.velocidad / 127))
        self.risas = [_texto("IA-IA!", tam, (90, 60, 40), angulo=12), _texto("IIIA-OOO!", tam, (90, 60, 40), angulo=-12)]

    def sprites(self, t):
        f = self.fuera(t)
        ta = self.t_arriba(t)
        out = []
        for lado, desfase in ((1, 0), (-1, 5)):  # 1: entra por la izquierda mirando a la derecha
            tt = ta - desfase
            riendo = tt >= 0 and t < self.n_sub + self.n_arriba
            b = int(round((0.5 + 0.5 * math.sin(tt * 0.9)) * 3)) if riendo else 0
            im = self.frames[(b, 1 if riendo else 0, lado)]
            asoma = self.ancho * 0.72 * f
            x = int(-self.ancho + asoma) if lado == 1 else int(self.W - asoma)
            y = int(self.H * 0.42 + (math.sin(tt * 0.45) * 8 * self.escala if riendo else 0))
            out.append((im, x, y))
            if riendo and (tt // int(self.fps * 0.7)) % 2 == 0:
                txt = self.risas[0 if lado == 1 else 1]
                tx = x + self.ancho * (0.55 if lado == 1 else 0.05)
                tx = min(max(tx, 4), self.W - txt.width - 4)  # que no se salga de la pantalla
                out.append((txt, int(tx), int(y - txt.height * 0.6)))
        return out

    def x_interes(self, t):
        return self.W / 2


# ============================================================================
# Motocultor con mucho humo
# ============================================================================

def dibujar_motocultor(k, fase, paso):
    """Motocultor viejo con pagès de capell de palla caminando detrás. Mira a la derecha.
    fase 0..1 gira la fresa y la rueda; paso 0..3 las piernas. Dibujo en modulos/sprite_campo.py."""
    return _sprite_campo.motocultor(k, fase, paso, suavizado=2)


class Motocultor(EventoDeCruce):
    """Motocultor por el camí, lento y echando humo negro a lo bestia."""
    capa = "fondo"
    SEG = 20
    SEG_ENTRA, SEG_SALE = 2.5, 2.5

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        self.velocidad = 100
        k = SS * 0.8 * self.escala
        esp = self.dir == -1
        self.frames = [[_reducir(dibujar_motocultor(k, i / 6, p), esp) for p in range(4)] for i in range(6)]
        self.frames_vuelta = [[im.transpose(Image.FLIP_LEFT_RIGHT) for im in fila] for fila in self.frames]
        self.ancho = self.frames[0][0].width
        self.alto = self.frames[0][0].height
        self.duracion = int(self.SEG * fps)
        self.humo = []
        for e in range(16):
            r = int((10 + 4 * e) * self.escala)
            im = Image.new("RGBA", (2 * r + 2, 2 * r + 2), (0, 0, 0, 0))
            gris = int(50 + 10 * e)
            ImageDraw.Draw(im).ellipse([1, 1, 2 * r, 2 * r], fill=(gris, gris, gris, int(220 * (1 - e / 16))))
            self.humo.append(im)
        self.rng = random.Random(rng.random())
        self.desv = [self.rng.uniform(-1, 1) for _ in range(40)]

    def _pos(self, t):
        x = self.x_lineal(t, self.ancho, self.SEG)
        y = int(Y_CAMI * self.H) - self.alto + int(6 * self.escala) - int(abs(math.sin(t * 1.3)) * 2)
        return x, y

    def sprites(self, t):
        x, y = self._pos(t)
        dir_ = -self.dir if self._saliendo else self.dir  # hacia dónde mira/avanza ahora mismo
        esc = self.ancho * (182 / 240)
        ex = x + (esc if dir_ == 1 else self.ancho - esc)
        ey = y + self.alto * (80 / 190)
        out = []
        n = 14  # muchas bocanadas: es un motocultor viejo
        for j in range(n):
            edad = (t / 2 + j * 16 / n) % 16
            im = self.humo[int(edad)]
            hx = ex - dir_ * edad * 9 * self.escala + self.desv[j] * edad * 2 - im.width / 2
            hy = ey - edad * 9 * self.escala - im.height / 2
            out.append((im, int(hx), int(hy)))
        frames = self.frames_vuelta if self._saliendo else self.frames
        out.append((frames[(t // 2) % 6][(t // 6) % 4], int(x), y))
        return out

    def x_interes(self, t):
        return self._pos(t)[0] + self.ancho / 2


# ============================================================================
# Bombilla: idea!
# ============================================================================

def dibujar_bombilla(k, encendida, brillo=1.0):
    w, h = int(240 * k), int(240 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy, r = 120, 104, 52
    if encendida:  # halo y rayos
        for i in range(6, 0, -1):
            rr = r + i * 11 * brillo
            a = int(28 * brillo)
            d.ellipse([(cx - rr) * k, (cy - rr) * k, (cx + rr) * k, (cy + rr) * k], fill=(255, 240, 120, a))
        for i in range(10):
            ang = math.radians(i * 36 + 18)
            r0, r1 = r + 18, r + 18 + 30 * brillo
            d.line([((cx + math.cos(ang) * r0) * k, (cy + math.sin(ang) * r0) * k),
                    ((cx + math.cos(ang) * r1) * k, (cy + math.sin(ang) * r1) * k)],
                   fill=(255, 220, 60, 230), width=max(2, int(6 * k)))
    cristal = (255, 236, 110) if encendida else (226, 232, 236)
    borde = (220, 170, 30) if encendida else (150, 160, 166)
    d.ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], fill=cristal, outline=borde,
              width=max(1, int(4 * k)))
    d.polygon([((cx - 26) * k, (cy + 40) * k), ((cx + 26) * k, (cy + 40) * k), ((cx + 20) * k, (cy + 66) * k),
               ((cx - 20) * k, (cy + 66) * k)], fill=cristal, outline=borde)
    d.ellipse([(cx - 30) * k, (cy - 34) * k, (cx - 12) * k, (cy - 12) * k], fill=(255, 255, 255, 200))  # reflejo
    fil = (240, 120, 20) if encendida else (120, 120, 120)  # filamento
    d.line([((cx - 12) * k, (cy + 40) * k), ((cx - 12) * k, (cy + 8) * k), ((cx - 4) * k, (cy - 4) * k),
            ((cx + 4) * k, (cy + 8) * k), ((cx + 12) * k, (cy - 4) * k), ((cx + 12) * k, (cy + 40) * k)],
           fill=fil, width=max(1, int(3 * k)))
    for i in range(4):  # rosca
        y = cy + 66 + i * 8
        d.rounded_rectangle([(cx - 20) * k, y * k, (cx + 20) * k, (y + 7) * k], radius=int(3 * k),
                            fill=(170, 170, 176), outline=(110, 110, 116))
    d.rectangle([(cx - 8) * k, (cy + 98) * k, (cx + 8) * k, (cy + 106) * k], fill=(60, 60, 64))
    return img.rotate(180, resample=Image.BICUBIC)  # cuelga del cable: rosca arriba


class Bombilla(Asoma):
    """Baja colgada de un cable, parpadea, se enciende (¡idea!) y vuelve a subir."""
    capa = "frente"
    SUBIR, BAJAR, MIN_ARRIBA, POR_DEFECTO = 0.6, 0.5, 1.2, 2.5

    def dibujar(self):
        k = SS * (0.55 + 0.25 * self.velocidad / 127) * self.escala
        self.apagada = _reducir(dibujar_bombilla(k, False))
        self.encendida = [_reducir(dibujar_bombilla(k, True, b)) for b in (0.6, 0.8, 1.0)]
        self.ancho, self.alto = self.apagada.size
        self.cx = self.rng.choice((0.5, 0.42, 0.58)) * self.W
        self.parpadeo = {2, 3, 6, 9, 10}  # fotogramas (tras bajar) con chispazo antes de encenderse
        self.t_on = 12

    def sprites(self, t):
        ta = self.t_arriba(t)
        if ta < 0 or ta in (set(range(self.t_on)) - self.parpadeo) or t >= self.n_sub + self.n_arriba:
            im = self.apagada
        else:
            im = self.encendida[int(1 + math.sin(t * 0.6))]
        largo = self.H * 0.12 * self.fuera(t)  # cable que baja desde arriba
        cable = Image.new("RGBA", (max(3, int(5 * self.escala)), max(1, int(largo) + 4)), (40, 40, 44, 255))
        bx = int(self.cx - im.width / 2)
        by = int(largo + self.alto * 0.42 * self.fuera(t) - im.height * 0.5 - self.alto * (1 - self.fuera(t)) * 0.6)
        return [(cable, int(self.cx - cable.width / 2), 0), (im, bx, by)]

    def x_interes(self, t):
        return self.cx


# ============================================================================
# Cabra: redoble de tambor y una coz
# ============================================================================

def _estallido(d, cx, cy, k, color=(255, 246, 200), n=7, r0=5, r1=24, ancho=3):
    """Rayas cortas que irradian desde (cx, cy): marca de impacto, bien visible."""
    for i in range(n):
        ang = math.radians(i * (360 / n) + 11)
        x0, y0 = cx + math.cos(ang) * r0, cy + math.sin(ang) * r0
        x1, y1 = cx + math.cos(ang) * r1, cy + math.sin(ang) * r1
        d.line([(x0 * k, y0 * k), (x1 * k, y1 * k)], fill=color, width=max(1, int(ancho * k)))


def dibujar_payes_tambor(k, fase, golpe=False):
    """Flabioler con ropa de pagès tocando flabiol y tamborí (ver modulos/sprite_payes_tambor.py).
    fase par/impar: baqueta arriba/abajo (el redoble). golpe=True: el instante de la coz,
    con el tamborí despedido y chispeando y el músico dando un respingo.
    El tamborí queda a la derecha del dibujo; Cabra lo espeja si la cabra viene por la izquierda."""
    return _sprite_payes.dibujar(k, fase, golpe, suavizado=2)


def dibujar_cabra(k, fase=0.0, impacto=False):
    """
    Cabra mallorquina de perfil, mirando a la derecha (ver modulos/sprite_cabra.py).
    fase 0: de pie, las cuatro patas en el suelo. Hacia 1, el cuerpo bascula sobre
    las delanteras y las traseras salen disparadas hacia atrás, a la altura del
    tamborí. impacto=True añade el estallido en las pezuñas.
    k ya incluye el supersampling (SS) del resto de eventos, así que basta con
    suavizar un poco más.
    """
    return _sprite_cabra.dibujar(k, fase, impacto, suavizado=2)


_PASOS_COZ = (0.0, 0.25, 0.5, 0.7, 0.85, 1.0)  # fases cacheadas de la coz (sin repintar cada fotograma)


def _paso_coz(fase):
    return min(_PASOS_COZ, key=lambda p: abs(p - fase))


class Cabra(Asoma):
    """
    Un payès se queda junto a la orilla tocando el tamborí sin parar (el
    redoble); a media nota, una cabra entra corriendo desde un lado, se para,
    se da la vuelta bien visiblemente y le suelta una coz con las patas
    traseras al tamborí (con estallido en la pata y en el tamborí, y este
    saliendo despedido, para que el golpe sea inconfundible), y se esconde
    otra vez por donde ha venido.
    """
    SUBIR, BAJAR, MIN_ARRIBA, POR_DEFECTO = 0.4, 0.4, 1.8, 2.5
    AJUSTA_CENIT = True  # por MIDI, la nota marca la coz, no cuando empieza a subir el payès

    def dibujar(self):
        k = SS * (1.1 + 0.4 * self.velocidad / 127) * self.escala
        # con --assets: sprites_editables/eventos/payes_tambor_0..1.png y payes_tambor_golpe_0..1.png
        self.payes = _marcos(self.assets, "payes_tambor", dibujar_payes_tambor, k, [0, 1])
        self.payes_golpe = _marcos(self.assets, "payes_tambor_golpe",
                                   lambda k_, f_: dibujar_payes_tambor(k_, f_, golpe=True), k, [0, 1])
        kc = k * 1.0  # la cabra nueva deja sitio a la coz en el lienzo: algo más grande para compensar
        # False/True de espejado puro (sin dir): mira a la derecha / a la izquierda
        # con --assets se usan sprites_editables/eventos/cabra_*.png y cabra_coz_0.png
        # si existen (ver crear_sprites_cabra.py); si no, el dibujo por código
        self.cabra = {}
        pasos = _marcos(self.assets, "cabra", dibujar_cabra, kc, list(_PASOS_COZ))
        for fase, im in zip(_PASOS_COZ, pasos):
            self.cabra[(fase, False, False)] = im
            self.cabra[(fase, False, True)] = im.transpose(Image.FLIP_LEFT_RIGHT)
        imp = _marcos(self.assets, "cabra_coz", lambda k_, _p: dibujar_cabra(k_, 1.0, impacto=True), kc, [1.0])[0]
        self.cabra[(1.0, True, False)] = imp
        self.cabra[(1.0, True, True)] = imp.transpose(Image.FLIP_LEFT_RIGHT)
        self.ancho_payes, self.alto = self.payes[0].size
        self.ancho_cabra = self.cabra[(0.0, False, False)].width
        self.cx = self.rng.choice((0.4, 0.6)) * self.W  # entre las dos ranas, lejos de los micros
        self.lado = self.rng.choice((1, -1))  # 1: entra por la izquierda
        if self.lado == 1:  # el tamborí tiene que quedar del lado por el que llega la cabra
            self.payes = [im.transpose(Image.FLIP_LEFT_RIGHT) for im in self.payes]
            self.payes_golpe = [im.transpose(Image.FLIP_LEFT_RIGHT) for im in self.payes_golpe]
        # al entrar mira hacia el payès (hacia la derecha si viene de la izquierda);
        # para que la coz conecte de verdad tiene que golpear de espaldas, así que
        # antes de cocear se para y se gira bien visiblemente (un par de fotogramas
        # de perfil "de canto", como un giro de dibujo animado) y queda mirando
        # para el otro lado
        self.mira_al_entrar = self.lado == -1
        n = self.n_arriba
        self.dur_dash = max(6, int(0.5 * self.fps))
        self.dur_gira = max(4, int(0.18 * self.fps))
        self.dur_kick = max(10, int(0.55 * self.fps))
        self.t_entra_cabra = max(0, int(n * 0.3))
        self.t_llega = self.t_entra_cabra + self.dur_dash
        self.t_gira_fin = self.t_llega + self.dur_gira
        self.t_vuelve = self.t_gira_fin + self.dur_kick
        self.t_sale_cabra = self.t_vuelve + self.dur_dash
        # ventana de impacto dentro de la coz: un hueco claro donde se queda en
        # pleno golpe (con estallido), ni un instante suelto ni demasiado largo
        self.p_windup, self.p_impacto = 0.45, 0.68
        self.x_lejos = -self.ancho_cabra if self.lado == 1 else self.W + self.ancho_cabra
        self.x_contacto = self.cx - self.lado * (self.ancho_payes * 0.5 + self.ancho_cabra * 0.25)

    def _cabra_estado(self, ta):
        """(x, fase 0..1, impacto, espejo, ancho_rel) de la cabra, o None si no está en pantalla.
        ancho_rel < 1 durante el giro: se encoge de lado para simular el cambio de cara."""
        if ta < self.t_entra_cabra or ta >= self.t_sale_cabra:
            return None
        if ta < self.t_llega:  # dash de entrada, mirando al payès
            p = (ta - self.t_entra_cabra) / self.dur_dash
            x = self.x_lejos + p * (self.x_contacto - self.x_lejos)
            return x, 0.0, False, self.mira_al_entrar, 1.0
        if ta < self.t_gira_fin:  # giro en el sitio: se encoge y vuelve a crecer ya del otro lado
            p = (ta - self.t_llega) / self.dur_gira
            mitad = 0.5
            if p < mitad:
                ancho_rel = max(0.1, 1.0 - p / mitad)
                espejo = self.mira_al_entrar
            else:
                ancho_rel = max(0.1, (p - mitad) / (1.0 - mitad))
                espejo = not self.mira_al_entrar
            return self.x_contacto, 0.0, False, espejo, ancho_rel
        if ta < self.t_vuelve:  # la coz: subida, impacto sostenido y bajada, ya de espaldas
            p = (ta - self.t_gira_fin) / self.dur_kick
            if p < self.p_windup:
                fase = (p / self.p_windup) ** 0.6  # entra rápido en el golpe
                impacto = False
            elif p < self.p_impacto:
                fase, impacto = 1.0, True
            else:
                resto = (p - self.p_impacto) / (1.0 - self.p_impacto)
                fase = max(0.0, 1.0 - resto ** 0.6)
                impacto = False
            return self.x_contacto, fase, impacto, not self.mira_al_entrar, 1.0
        p = (ta - self.t_vuelve) / self.dur_dash  # dash de salida, ya de vuelta a mirar hacia dentro
        x = self.x_contacto + p * (self.x_lejos - self.x_contacto)
        return x, 0.0, False, not self.mira_al_entrar, 1.0

    def sprites(self, t):
        f = self.fuera(t)
        ta = self.t_arriba(t)
        estado = self._cabra_estado(ta) if ta >= 0 else None
        en_impacto = estado is not None and estado[2]
        payes_frames = self.payes_golpe if en_impacto else self.payes
        im = payes_frames[(t // 2) % 2]
        y = int(Y_FRENTE * self.H - self.alto * f)  # de pie en el suelo, no asomando por el borde
        bote = 0
        if estado is not None:
            bote = int((16 if en_impacto else 6) * self.escala) if estado[1] > 0 or en_impacto else 0
        out = [(im, int(self.cx - self.ancho_payes / 2), y - bote)]
        if estado is not None:
            x, fase, impacto, espejo, ancho_rel = estado
            cim = self.cabra[(_paso_coz(fase), impacto, espejo)]
            if ancho_rel < 0.999:
                w = max(1, int(cim.width * ancho_rel))
                cim = cim.resize((w, cim.height))
            out.append((cim, int(x - cim.width / 2), int(y + self.alto - cim.height)))
        return out

    def x_interes(self, t):
        return self.cx


TIPOS.update({
    "cerdo_asoma": CerdoAsoma,
    "grillo": Grillo,
    "rana_guapa": RanaGuapa,
    "pedo": Pedo,
    "muchedumbre": Muchedumbre,
    "asnos": Asnos,
    "motocultor": Motocultor,
    "bombilla": Bombilla,
    "cabra": Cabra,
})
