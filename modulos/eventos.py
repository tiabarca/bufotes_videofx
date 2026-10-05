"""
Eventos que pasan por la escena mientras las ranas hablan:
tractor por el camí (detrás), dos pájaros por el cielo, y por delante de
las ranas un porc negre que se para a husmear y un gusano que se arrastra.

Cada evento tiene:
  - capa: "fondo" (detrás de las ranas) o "frente" (delante)
  - duracion en fotogramas
  - sprites(t) -> lista de (imagen RGBA, x, y) para el fotograma t del evento
  - x_interes(t) -> posición x a la que miran las ranas (o None)

Los fotogramas de cada animación se dibujan una sola vez al empezar.
"""

import math
import os
import random

from PIL import Image, ImageDraw

from . import sprite_colla as _sprite_colla

from .escena import X_RANAS, Y_CAMI, Y_FRENTE

SS = 2  # supersampling de los sprites


def _reducir(img, espejo=False):
    img = img.resize((max(1, img.width // SS), max(1, img.height // SS)), Image.LANCZOS)
    return img.transpose(Image.FLIP_LEFT_RIGHT) if espejo else img


def _marcos(assets, clave, dibujar_fn, k, params, espejo=False):
    """
    Fotogramas de un personaje de evento: uno por valor de `params`, pasado a
    `dibujar_fn(k, param)`. Si existe `assets/eventos/{clave}_{i}.png` se usa
    ese PNG en su lugar (reescalado al tamaño que tendría el dibujo por
    código, así que vale cualquier resolución y funciona a cualquier --alto).
    Ver exportar_sprites.py para sacar la plantilla de cada personaje.
    """
    out = []
    for i, param in enumerate(params):
        base = dibujar_fn(k, param)
        ruta = os.path.join(assets, "eventos", f"{clave}_{i}.png") if assets else None
        if ruta and os.path.exists(ruta):
            base = Image.open(ruta).convert("RGBA").resize(base.size, Image.LANCZOS)
        out.append(_reducir(base, espejo))
    return out


# ----------------------------------------------------------------------------
# Dibujos (en unidades de diseño; `k` escala a píxeles)
# ----------------------------------------------------------------------------

def dibujar_tractor(k, fase):
    """Tractor rojo clásico con pagès de gorra. fase 0..1 gira las ruedas. Mira a la derecha."""
    w, h = int(260 * k), int(190 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def R(x0, y0, x1, y1, **kw):
        d.rectangle([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    def E(x0, y0, x1, y1, **kw):
        d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    rojo, rojo_osc, negro = (196, 44, 36), (150, 30, 26), (34, 32, 32)
    # escape
    R(150, 38, 158, 92, fill=(70, 66, 64))
    # cabina (arco de seguridad)
    R(52, 40, 60, 118, fill=(60, 60, 64))
    R(52, 40, 118, 48, fill=(60, 60, 64))
    R(112, 40, 120, 104, fill=(60, 60, 64))
    # pagès
    E(72, 58, 98, 84, fill=(236, 190, 160))           # cara
    d.chord([70 * k, 50 * k, 100 * k, 72 * k], 180, 360, fill=(90, 80, 70))  # gorra
    R(90, 60, 106, 64, fill=(90, 80, 70))              # visera
    E(84, 66, 88, 70, fill=negro)                      # ojo
    R(72, 84, 98, 112, fill=(70, 100, 150))            # camisa
    # capó y chasis
    R(105, 88, 232, 128, fill=rojo, outline=rojo_osc, width=max(1, int(3 * k)))
    R(45, 108, 150, 138, fill=rojo, outline=rojo_osc, width=max(1, int(3 * k)))
    for i in range(5):  # rejilla
        R(214, 94 + i * 7, 230, 97 + i * 7, fill=rojo_osc)
    E(222, 96, 234, 108, fill=(250, 230, 150))         # faro

    # ruedas con radios que giran
    def rueda(cx, cy, r, radios):
        E(cx - r, cy - r, cx + r, cy + r, fill=negro)
        for i in range(16):  # tacos
            a = 2 * math.pi * (i / 16 + fase * 0.25)
            d.line([((cx + math.cos(a) * r * 0.86) * k, (cy + math.sin(a) * r * 0.86) * k),
                    ((cx + math.cos(a) * r) * k, (cy + math.sin(a) * r) * k)],
                   fill=(70, 66, 64), width=max(1, int(4 * k)))
        E(cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62, fill=(236, 190, 40))
        for i in range(radios):
            a = 2 * math.pi * (i / radios + fase / radios)
            d.line([(cx * k, cy * k), ((cx + math.cos(a) * r * 0.58) * k, (cy + math.sin(a) * r * 0.58) * k)],
                   fill=(180, 140, 20), width=max(1, int(5 * k)))
        E(cx - r * 0.18, cy - r * 0.18, cx + r * 0.18, cy + r * 0.18, fill=(120, 110, 100))

    rueda(70, 130, 56, 6)
    rueda(200, 150, 34, 5)
    return img


def dibujar_humo(k, edad):
    """Bocanada de humo: crece y se desvanece con la edad (0..1)."""
    r = int((8 + 22 * edad) * k)
    img = Image.new("RGBA", (2 * r + 2, 2 * r + 2), (0, 0, 0, 0))
    a = int(160 * (1 - edad))
    ImageDraw.Draw(img).ellipse([1, 1, 2 * r, 2 * r], fill=(210, 210, 210, a))
    return img


def dibujar_cerdo_corriendo(k, paso):
    """Porc negre corriendo despavorido, de perfil, con las patas muy abiertas. paso 0..3. Mira a la derecha."""
    w, h = int(150 * k), int(100 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    negro, gris, rosa = (38, 34, 38), (70, 64, 70), (150, 110, 120)

    def E(x0, y0, x1, y1, **kw):
        d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    osc = [0, 14, 0, -14][paso % 4]
    for i, (px, fase) in enumerate(((35, 1), (55, -1), (95, -1), (115, 1))):
        dx = osc * fase
        d.polygon([((px - 6) * k, 60 * k), ((px + 6) * k, 60 * k), ((px + 5 + dx) * k, 92 * k),
                   ((px - 5 + dx) * k, 92 * k)], fill=negro if i % 2 else gris)
    bote = [0, -3, 0, -1][paso % 4]  # el tren delantero también bota al galopar, si no queda tieso
    flap = [0, -6, -2, 3][paso % 4]  # la oreja ondea aparte, con su propio vaivén
    d.arc([10 * k, (20 + bote) * k, 32 * k, (42 + bote) * k], 60, 380, fill=negro,
          width=max(1, int(4 * k)))  # cola tiesa del susto
    E(18, 10 + bote, 132, 72 + bote, fill=negro)  # cuerpo estirado al galope
    E(115, 2 + bote, 148, 42 + bote, fill=negro)  # cabeza
    d.polygon([(122 * k, (6 + bote) * k), (130 * k, (-10 + bote + flap) * k),
               (138 * k, (8 + bote) * k)], fill=gris)  # oreja
    E(134, 16 + bote, 150, 32 + bote, fill=rosa)  # hocico
    E(128, 10 + bote, 134, 16 + bote, fill=(250, 250, 250))  # ojo muy abierto, del susto
    E(130, 11 + bote, 133, 14 + bote, fill=(10, 10, 10))
    return img


def dibujar_payes(k, paso, arma):
    """Payés corriendo con un cuchillo o una olla en alto. paso 0..3 anima las piernas. Mira a la derecha."""
    w, h = int(100 * k), int(130 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    piel, camisa, oscuro = (228, 182, 150), (205, 65, 55), (40, 36, 40)

    def E(x0, y0, x1, y1, **kw):
        d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    def R(x0, y0, x1, y1, **kw):
        d.rectangle([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    osc = [0, 16, 0, -16][paso % 4]
    for px, fase in ((30, 1), (50, -1)):  # piernas a la carrera
        dx = osc * fase
        d.polygon([((px - 6) * k, 78 * k), ((px + 6) * k, 78 * k), ((px + 4 + dx) * k, 120 * k),
                   ((px - 8 + dx) * k, 120 * k)], fill=oscuro)
    R(18, 40, 62, 82, fill=camisa)  # cuerpo
    d.line([(20 * k, 50 * k), (4 * k, 32 * k)], fill=piel, width=max(1, int(6 * k)))  # brazo de atrás
    E(24, 10, 58, 44, fill=piel)  # cabeza
    d.chord([20 * k, 2 * k, 62 * k, 26 * k], 180, 360, fill=(90, 80, 70))  # gorra de pagès

    sube = 10 if paso % 2 == 0 else 2  # el brazo del arma sube y baja al correr
    d.line([(58 * k, 46 * k), (80 * k, (24 - sube) * k)], fill=piel, width=max(1, int(7 * k)))
    if arma == "cuchillo":
        d.polygon([(76 * k, (20 - sube) * k), (94 * k, (6 - sube) * k), (82 * k, (26 - sube) * k)],
                   fill=(215, 215, 220), outline=oscuro)
    else:  # olla, a modo de instrumento de percusión improvisado
        E(68, 6 - sube, 94, 26 - sube, fill=(120, 120, 128), outline=oscuro, width=max(1, int(2 * k)))
        R(74, 0 - sube, 88, 8 - sube, fill=(95, 95, 102))
    return img


def dibujar_pajaro(k, ala):
    """Pájaro en silueta con aleteo. ala 0..1 (0 alas arriba, 1 abajo). Mira a la derecha."""
    w, h = int(90 * k), int(70 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = (40, 44, 58)
    punta = 8 + 50 * ala      # y de la punta del ala
    codo = 22 + 22 * ala
    for lado in (-1, 1):
        d.line([(45 * k, 36 * k), ((45 + lado * 18) * k, codo * k), ((45 + lado * 42) * k, punta * k)],
               fill=c, width=max(2, int(6 * k)), joint="curve")
    d.ellipse([34 * k, 30 * k, 62 * k, 42 * k], fill=c)
    d.ellipse([56 * k, 28 * k, 68 * k, 38 * k], fill=c)
    d.polygon([(67 * k, 32 * k), (75 * k, 34 * k), (67 * k, 36 * k)], fill=(220, 160, 40))
    d.polygon([(34 * k, 34 * k), (22 * k, 30 * k), (22 * k, 42 * k)], fill=c)
    return img


def dibujar_gusano(k, fase):
    """Gusano verde que avanza ondulando. fase 0..1. Mira a la derecha."""
    n = 11
    w, h = int(200 * k), int(70 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(n):  # de la cola a la cabeza
        t = i / (n - 1)
        x = 20 + t * 150
        y = 46 - max(0.0, math.sin(2 * math.pi * (fase - t * 0.9))) * 16
        r = 11 + 3 * math.sin(math.pi * t)
        tono = (110 + int(40 * (i % 2)), 180 + int(20 * (i % 2)), 70)
        d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=tono, outline=(70, 130, 50),
                  width=max(1, int(2 * k)))
    # cabeza
    yh = 46 - max(0.0, math.sin(2 * math.pi * (fase - 0.95))) * 16
    d.ellipse([160 * k, (yh - 17) * k, 194 * k, (yh + 15) * k], fill=(150, 205, 90), outline=(70, 130, 50),
              width=max(1, int(2 * k)))
    d.ellipse([176 * k, (yh - 10) * k, 188 * k, (yh + 2) * k], fill=(255, 255, 255))
    d.ellipse([180 * k, (yh - 7) * k, 187 * k, (yh) * k], fill=(15, 15, 15))
    d.arc([172 * k, (yh - 2) * k, 190 * k, (yh + 10) * k], 20, 150, fill=(40, 80, 30), width=max(1, int(2 * k)))
    d.line([(172 * k, (yh - 15) * k), (168 * k, (yh - 28) * k)], fill=(70, 130, 50), width=max(1, int(2 * k)))
    d.ellipse([164 * k, (yh - 33) * k, 172 * k, (yh - 25) * k], fill=(240, 120, 120))
    return img


def dibujar_mosquito(k, fase):
    """Mosquito pequeño, visto de perfil. fase 0..7 anima el aleteo."""
    w, h = int(44 * k), int(30 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cuerpo, ala = (45, 42, 44), (215, 220, 230, 150)
    bate = 6 * abs(math.sin(fase / 4 * math.pi))  # aleteo rápido

    d.line([(18 * k, 15 * k), (2 * k, 10 * k)], fill=cuerpo, width=max(1, int(1.2 * k)))  # trompa
    d.ellipse([16 * k, 9 * k, 32 * k, 19 * k], fill=cuerpo)  # cuerpo
    d.ellipse([20 * k, (4 - bate) * k, 40 * k, (14 - bate) * k], fill=ala)  # ala arriba
    d.ellipse([20 * k, (14 + bate) * k, 40 * k, (24 + bate) * k], fill=ala)  # ala abajo
    for i in range(3):  # patas finas
        d.line([((20 + i * 3) * k, 18 * k), ((14 + i * 3) * k, 28 * k)], fill=cuerpo, width=max(1, int(k)))
    return img


def dibujar_oveja(k, pasto=0.0):
    """Oveja de perfil, lanuda. pasto 0..1 agacha la cabeza a pastar. Mira a la derecha."""
    w, h = int(90 * k), int(68 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lana, sombra, negro = (248, 246, 240), (220, 216, 206), (45, 42, 40)

    def E(x0, y0, x1, y1, **kw):
        d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    for px in (22, 34, 56, 68):  # patas
        d.rectangle([(px - 3) * k, 46 * k, (px + 3) * k, 64 * k], fill=negro)
    for cx, cy, r in ((44, 34, 22), (26, 36, 15), (60, 36, 15), (36, 24, 13), (52, 24, 13)):  # lana a bultos
        E(cx - r, cy - r * 0.85, cx + r, cy + r * 0.85, fill=lana, outline=sombra, width=max(1, int(k)))
    dy = 14 * pasto  # la cabeza se agacha al pastar
    E(70, 20 + dy, 88, 38 + dy, fill=negro)
    E(73, 25 + dy, 77, 29 + dy, fill=(95, 90, 86))
    return img


def dibujar_perro(k, paso=0):
    """Perro pastor corriendo tras el rebaño. paso 0..3 anima las patas. Mira a la derecha."""
    w, h = int(100 * k), int(76 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pelo, oscuro = (122, 92, 56), (72, 52, 32)
    osc = [0, 9, 0, -9][paso % 4]
    for px, fase in ((20, 1), (35, -1), (62, -1), (77, 1)):
        dx = osc * fase
        d.line([(px * k, 46 * k), ((px + dx) * k, 68 * k)], fill=oscuro, width=max(1, int(5 * k)))
    d.polygon([(8 * k, 28 * k), (20 * k, 14 * k), (24 * k, 32 * k)], fill=oscuro)  # cola
    d.ellipse([16 * k, 20 * k, 76 * k, 52 * k], fill=pelo, outline=oscuro, width=max(1, int(2 * k)))  # cuerpo
    d.ellipse([70 * k, 12 * k, 96 * k, 36 * k], fill=pelo, outline=oscuro, width=max(1, int(2 * k)))  # cabeza
    d.polygon([(78 * k, 10 * k), (82 * k, -2 * k), (88 * k, 12 * k)], fill=oscuro)  # oreja
    d.ellipse([90 * k, 20 * k, 96 * k, 26 * k], fill=(30, 25, 20))  # morro
    return img


def dibujar_xeremier(k, paso):
    """Xeremier: toca la xeremia (gaita mallorquina) mientras camina. paso 0..3 anima las piernas.
    Dibujo en modulos/sprite_colla.py."""
    return _sprite_colla.dibujar_xeremier(k, paso, suavizado=2)


def dibujar_fabioler(k, paso):
    """Flabiolaire: flabiol con una mano y tamborí con la otra. paso 0..3 anima las piernas.
    Dibujo en modulos/sprite_colla.py."""
    return _sprite_colla.dibujar_fabioler(k, paso, suavizado=2)


def dibujar_payes_baila(k, fase):
    """Ballador de ball de bot: salta con los brazos en alto y castanyoles. fase 0..3.
    Dibujo en modulos/sprite_colla.py."""
    return _sprite_colla.dibujar_payes_baila(k, fase, suavizado=2)


def dibujar_payesa_baila(k, fase):
    """Balladora con rebosillo, cosset y faldilla de vuelo; castanyoles. fase 0..3.
    Dibujo en modulos/sprite_colla.py."""
    return _sprite_colla.dibujar_payesa_baila(k, fase, suavizado=2)


def dibujar_payes_dret(k, balanceo=0):
    """Payés de pie y quieto (con un ligero balanceo), plantado delante de la puerta."""
    w, h = int(70 * k), int(120 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    piel, camisa, pantalon, oscuro = (228, 182, 150), (70, 120, 160), (90, 80, 70), (40, 36, 40)

    def E(x0, y0, x1, y1, **kw):
        d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    d.polygon([(26 * k, 70 * k), (32 * k, 70 * k), (30 * k + balanceo, 110 * k), (22 * k + balanceo, 110 * k)],
              fill=pantalon)
    d.polygon([(38 * k, 70 * k), (44 * k, 70 * k), (48 * k - balanceo, 110 * k), (40 * k - balanceo, 110 * k)],
              fill=pantalon)
    d.rectangle([18 * k, 32 * k, 52 * k, 72 * k], fill=camisa)
    E(22, 2, 50, 30, fill=piel)
    d.chord([18 * k, -6 * k, 54 * k, 14 * k], 180, 360, fill=(90, 80, 70))  # gorra
    d.line([(18 * k, 40 * k), (8 * k, 56 * k)], fill=piel, width=max(1, int(5 * k)))  # brazos
    d.line([(52 * k, 40 * k), (62 * k, 56 * k)], fill=piel, width=max(1, int(5 * k)))
    return img


def dibujar_payesa_ventana(k, agita):
    """Payesa asomada a una ventana, amenazando con un palo. agita 0..1: el palo se mueve de lado a lado."""
    w, h = int(80 * k), int(70 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    piel, blusa, panuelo, palo = (228, 182, 150), (250, 248, 240), (210, 70, 90), (110, 80, 55)

    def E(x0, y0, x1, y1, **kw):
        d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    d.rectangle([14 * k, 30 * k, 56 * k, 70 * k], fill=blusa)  # torso asomado
    E(18, 4, 48, 34, fill=piel)
    d.chord([14 * k, -4 * k, 52 * k, 18 * k], 180, 360, fill=panuelo)
    ang = math.radians(-35 + agita * 55)  # el palo se agita de lado a lado
    ex, ey = 50 * k + math.cos(ang) * 28 * k, 20 * k + math.sin(ang) * 28 * k
    d.line([(48 * k, 26 * k), (ex, ey)], fill=palo, width=max(1, int(4 * k)))
    d.line([(48 * k, 26 * k), (56 * k, 36 * k)], fill=piel, width=max(1, int(5 * k)))  # brazo sujetando
    return img


# ----------------------------------------------------------------------------
# Eventos
# ----------------------------------------------------------------------------

class Evento:
    capa = "fondo"

    def __init__(self, W, H, fps, rng, assets=None):
        self.W, self.H, self.fps = W, H, fps
        self.dir = rng.choice((1, -1))  # 1: de izquierda a derecha
        self.escala = H / 720
        self.assets = assets

    def x_lineal(self, t, ancho, segundos):
        """Cruza la pantalla de un lado a otro en `segundos`."""
        p = t / (segundos * self.fps)
        x = -ancho + p * (self.W + 2 * ancho)
        return x if self.dir == 1 else self.W - x - ancho

    def x_interes(self, t):
        return None


class EventoDeCruce(Evento):
    """
    Base para los eventos que cruzan la pantalla con x_lineal (tractor,
    cerdo, pájaros, ovejas, motocultor, grillo). Al salir al azar cruzan de
    un tirón en self.SEG segundos, como siempre. Lanzados desde MIDI, en
    cambio, entran, se quedan quietos mientras dura la nota y salen
    girando por donde han entrado: la duración real del evento depende de
    cuánto se mantenga la nota, no de self.SEG.

    Las subclases no tienen que tocar su _pos/sprites: solo precalcular
    también los fotogramas espejados (ida y vuelta) y, en sprites(), usar
    self._saliendo para elegir unos u otros.
    """
    SEG_ENTRA, SEG_SALE, MIN_ESPERA = 1.5, 1.5, 1.0

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        self._nota = False
        self._saliendo = False

    def ajustar_a_nota(self):
        self._nota = True
        self.f_entra = max(1, int(self.SEG_ENTRA * self.fps))
        self.f_espera = max(int(self.MIN_ESPERA * self.fps), self.mantener)
        self.f_sale = max(1, int(self.SEG_SALE * self.fps))
        self.duracion = self.f_entra + self.f_espera + self.f_sale

    def x_lineal(self, t, ancho, segundos):
        if not self._nota:
            return super().x_lineal(t, ancho, segundos)
        x_fuera = -ancho if self.dir == 1 else self.W + ancho
        x_dentro = 0.5 * self.W
        if t < self.f_entra:
            self._saliendo = False
            return x_fuera + (t / self.f_entra) * (x_dentro - x_fuera)
        if t < self.f_entra + self.f_espera:
            self._saliendo = False
            return x_dentro
        self._saliendo = True
        p = min(1.0, (t - self.f_entra - self.f_espera) / self.f_sale)
        return x_dentro + p * (x_fuera - x_dentro)


class Tractor(EventoDeCruce):
    capa = "fondo"
    SEG = 13

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        k = SS * 0.55 * self.escala
        esp = self.dir == -1
        self.frames = _marcos(assets, "tractor", dibujar_tractor, k, [i / 8 for i in range(8)], esp)
        self.frames_vuelta = [im.transpose(Image.FLIP_LEFT_RIGHT) for im in self.frames]
        self.humo = [_reducir(dibujar_humo(k, e / 10)) for e in range(10)]
        self.duracion = int(self.SEG * fps)
        self.ancho = self.frames[0].width

    def _pos(self, t):
        x = self.x_lineal(t, self.ancho, self.SEG)
        bote = int(abs(math.sin(t * 0.9)) * 2 * self.escala)
        y = int(Y_CAMI * self.H) - self.frames[0].height - bote + int(4 * self.escala)
        return x, y

    def sprites(self, t):
        x, y = self._pos(t)
        frames = self.frames_vuelta if self._saliendo else self.frames
        dir_ = -self.dir if self._saliendo else self.dir  # hacia dónde mira/avanza ahora mismo
        out = []
        esc = self.frames[0].width * (152 / 260)  # posición del tubo de escape
        ex = x + (esc if dir_ == 1 else self.frames[0].width - esc)
        for j in range(4):  # bocanadas que se quedan atrás y suben
            edad = ((t / 4 + j * 2.5) % 10)
            im = self.humo[int(edad)]
            hx = ex - dir_ * edad * 6 * self.escala - im.width / 2
            hy = y + 18 * self.escala - edad * 7 * self.escala - im.height / 2
            out.append((im, int(hx), int(hy)))
        out.append((frames[(t // 2) % 8], int(x), y))
        return out

    def x_interes(self, t):
        return self._pos(t)[0] + self.ancho / 2


class Cerdo(EventoDeCruce):
    """El porc negre huye por el camí con una muchedumbre de payeses detrás, cuchillo y olla en alto."""
    capa = "fondo"
    SEG = 11

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        k = SS * 0.75 * self.escala
        esp = self.dir == -1
        # el porc, la mitad de grande
        self.cerdo = _marcos(assets, "cerdo", dibujar_cerdo_corriendo, k * 0.5, list(range(4)), esp)
        self.cerdo_vuelta = [im.transpose(Image.FLIP_LEFT_RIGHT) for im in self.cerdo]
        self.ancho = self.cerdo[0].width
        n = rng.randint(4, 5)  # una muchedumbre de verdad
        self.payeses = []
        retraso_base = rng.uniform(0.4, 0.55)  # que no le vayan pisando los talones al porc
        for j in range(n):
            arma = "cuchillo" if j % 2 == 0 else "olla"
            dibujar = lambda k_, p, arma=arma: dibujar_payes(k_, p, arma)
            frames = _marcos(assets, f"payes_{arma}", dibujar, k * 0.8, list(range(4)), esp)
            frames_vuelta = [im.transpose(Image.FLIP_LEFT_RIGHT) for im in frames]
            retraso = retraso_base + j * rng.uniform(0.14, 0.22)  # cada uno un poco más atrás, desincronizados
            dy = rng.uniform(-4, 4) * self.escala
            self.payeses.append((frames, frames_vuelta, retraso, dy))
        self.y = (Y_CAMI - 0.03) * H  # junto al camí, cerca de por donde pasa el tractor
        self.duracion = int(self.SEG * fps)

    def _x(self, t, retraso=0.0):
        return self.x_lineal(t - retraso * self.fps, self.ancho, self.SEG)

    def sprites(self, t):
        out = []
        for frames, frames_vuelta, retraso, dy in self.payeses:
            x = self._x(t, retraso)
            fr = frames_vuelta if self._saliendo else frames
            im = fr[(t // 3) % 4]
            out.append((im, int(x), int(self.y - im.height + dy)))
        xc = self._x(t)
        cerdo = self.cerdo_vuelta if self._saliendo else self.cerdo
        out.append((cerdo[(t // 2) % 4], int(xc), int(self.y - self.cerdo[0].height)))
        return out

    def x_interes(self, t):
        return self._x(t) + self.ancho / 2


class Pajaros(EventoDeCruce):
    capa = "fondo"
    SEG = 9

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        esp = self.dir == -1
        params = [0.5 - 0.5 * math.cos(2 * math.pi * i / 8) for i in range(8)]
        self.frames = [
            _marcos(assets, "pajaro", dibujar_pajaro, SS * 1.0 * self.escala * s, params, esp)
            for s in (1.0, 0.8)
        ]
        self.frames_vuelta = [[im.transpose(Image.FLIP_LEFT_RIGHT) for im in grupo] for grupo in self.frames]
        self.duracion = int(self.SEG * fps)
        self.y0 = rng.uniform(0.08, 0.2)
        self.ancho = self.frames[0][0].width

    def _pos(self, t, n):
        desfase = n * 0.07 * self.W * (-self.dir)  # el segundo va algo detrás
        x = self.x_lineal(t, self.ancho * 2, self.SEG) + desfase
        y = (self.y0 + 0.03 * n) * self.H + math.sin(t / self.fps * 2.2 + n) * 0.02 * self.H
        return x, y

    def sprites(self, t):
        out = []
        for n in (1, 0):
            x, y = self._pos(t, n)
            frames = self.frames_vuelta if self._saliendo else self.frames
            im = frames[n][(t // 2 + n * 3) % 8]
            out.append((im, int(x), int(y)))
        return out

    def x_interes(self, t):
        return self._pos(t, 0)[0] + self.ancho / 2


class _Presa(Evento):
    """
    Base para "bichos que una rana caza con la lengua": cada subclase se
    encarga de su propio arrastre/vuelo hasta `frame_captura`, y esta clase
    pone en común la fase de lengüetazo (dispara, agarra, recoge) y el aviso
    a ranas.py para que la rana abra la boca mientras dura.

    Las subclases deben fijar en __init__: ancho, objetivo (índice de rana),
    x_boca, y_boca, y_suelo (punto donde se la atrapa), x_parada,
    frame_captura y duracion.
    """

    def _ext_lengua(self, t):
        """0 = lengua recogida, 1 = del todo estirada. Dispara rápido, recoge más despacio."""
        t2 = t - self.frame_captura
        total = max(self.duracion - self.frame_captura, 1)
        p = min(t2 / total, 1.0)
        return p / 0.3 if p < 0.3 else max(0.0, 1 - (p - 0.3) / 0.7)

    def _lengua(self, tx, ty):
        """Lienzo pequeño con la lengua (línea + punta redonda) desde la boca hasta (tx, ty)."""
        pad = max(3, int(6 * self.escala))
        x0, y0 = self.x_boca, self.y_boca
        minx, maxx = min(x0, tx) - pad, max(x0, tx) + pad
        miny, maxy = min(y0, ty) - pad, max(y0, ty) + pad
        w, h = max(1, int(maxx - minx)), max(1, int(maxy - miny))
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        rosa = (225, 95, 115)
        ancho = max(3, int(9 * self.escala))
        d.line([(x0 - minx, y0 - miny), (tx - minx, ty - miny)], fill=rosa, width=ancho)
        r = ancho * 1.3
        d.ellipse([tx - minx - r, ty - miny - r, tx - minx + r, ty - miny + r], fill=rosa)
        return img, int(minx), int(miny)

    def _sprites_captura(self, t, im_presa):
        """Lengua + la presa enganchada en la punta (mientras no haya vuelto casi del todo)."""
        ext = self._ext_lengua(t)
        tx = self.x_boca + (self.x_parada - self.x_boca) * ext
        ty = self.y_boca + (self.y_suelo - self.y_boca) * ext
        lengua, mx, my = self._lengua(tx, ty)
        out = [(lengua, mx, my)]
        if ext > 0.03:
            out.append((im_presa, int(tx - im_presa.width / 2), int(ty - im_presa.height / 2)))
        return out

    def boca_forzada(self, t):
        """(índice_rana, estado_boca): abre un poco la boca al lanzar la lengua, cierra al tragar."""
        if t < self.frame_captura:
            return None
        return (self.objetivo, 1 if self._ext_lengua(t) > 0.03 else 0)


class Gusano(_Presa):
    """Un gusano se arrastra hacia la primera rana que encuentra; al llegar, se lo come de un lengüetazo."""
    capa = "frente"
    VEL = 20  # segundos que tardaría en cruzar la pantalla entera, para mantener el mismo ritmo de antes

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        esp = self.dir == -1
        self.frames = _marcos(assets, "gusano", dibujar_gusano, SS * 0.6 * self.escala, [i / 16 for i in range(16)], esp)
        self.ancho = self.frames[0].width

        self.objetivo = 0 if self.dir == 1 else 1  # la primera rana que se cruza según hacia dónde va
        self.x_boca = X_RANAS[self.objetivo] * W
        self.y_boca = 0.66 * H  # dentro de la boca, hacia el labio inferior (no por encima, hacia los ojos)
        self.y_suelo = Y_FRENTE * H

        self.x_inicio = -self.ancho / 2 if self.dir == 1 else W + self.ancho / 2
        alcance = 0.045 * W  # desde aquí dispara la lengua, en vez de arrastrarse hasta la propia boca
        self.x_parada = self.x_boca + (-alcance if self.dir == 1 else alcance)

        self.seg_arrastre = max(1.0, abs(self.x_parada - self.x_inicio) / W * self.VEL)
        self.frame_captura = int(self.seg_arrastre * fps)
        self.seg_lengua = 0.4
        self.duracion = self.frame_captura + int(self.seg_lengua * fps)

    def sprites(self, t):
        if t < self.frame_captura:
            p = t / max(self.frame_captura, 1)
            x = self.x_inicio + p * (self.x_parada - self.x_inicio)
            im = self.frames[(t // 2) % 16]
            return [(im, int(x - self.ancho / 2), int(self.y_suelo) - im.height)]
        return self._sprites_captura(t, self.frames[0])

    def x_interes(self, t):
        if t < self.frame_captura:
            p = t / max(self.frame_captura, 1)
            return self.x_inicio + p * (self.x_parada - self.x_inicio)
        return None


class Mosquito(_Presa):
    """
    Un mosquito vuela errático por delante de las ranas; en cuanto ha pasado
    de la mitad de la pantalla, la rana hacia la que va se lo come de un
    lengüetazo (igual que el gusano, pero volando en vez de arrastrándose).
    """
    capa = "frente"
    VEL = 11  # vuela bastante más rápido que repta el gusano

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        self.frames = _marcos(assets, "mosquito", dibujar_mosquito, SS * 0.35 * self.escala, list(range(8)), False)
        self.ancho = self.frames[0].width

        # al pasar de la mitad va hacia la rana del lado contrario a por donde entró
        self.objetivo = 1 if self.dir == 1 else 0
        self.x_boca = X_RANAS[self.objetivo] * W
        self.y_boca = 0.66 * H
        self.y_base = rng.uniform(0.42, 0.58) * H
        self.y_suelo = self.y_base

        self.x_inicio = -self.ancho / 2 if self.dir == 1 else W + self.ancho / 2
        alcance = 0.04 * W
        self.x_parada = self.x_boca + (-alcance if self.dir == 1 else alcance)

        self.amp_x = rng.uniform(0.01, 0.02) * W
        self.amp_y = rng.uniform(0.03, 0.05) * H
        self.f1, self.f2 = rng.uniform(2.2, 3.4), rng.uniform(5.0, 7.5)
        self.fase1, self.fase2 = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)

        self.seg_vuelo = max(1.0, abs(self.x_parada - self.x_inicio) / W * self.VEL)
        self.frame_captura = int(self.seg_vuelo * fps)
        self.seg_lengua = 0.35
        self.duracion = self.frame_captura + int(self.seg_lengua * fps)

    def _pos(self, t):
        p = min(t, self.frame_captura) / max(self.frame_captura, 1)
        s = t / self.fps
        x = self.x_inicio + p * (self.x_parada - self.x_inicio) + self.amp_x * math.sin(
            2 * math.pi * self.f1 * s + self.fase1)
        y = self.y_base + self.amp_y * (0.6 * math.sin(2 * math.pi * self.f1 * 0.7 * s + self.fase1) +
                                         0.4 * math.sin(2 * math.pi * self.f2 * s + self.fase2))
        return x, y

    def sprites(self, t):
        if t < self.frame_captura:
            x, y = self._pos(t)
            im = self.frames[(t // 2) % len(self.frames)]
            return [(im, int(x - self.ancho / 2), int(y - im.height / 2))]
        return self._sprites_captura(t, self.frames[0])

    def x_interes(self, t):
        if t < self.frame_captura:
            return self._pos(t)[0]
        return None


class Ovejas(EventoDeCruce):
    """Un rebaño pasturando despacio por el campo, con un perro que lo persigue de un lado a otro."""
    capa = "fondo"
    SEG = 24  # 19 / 0.8: van a un 80% de la velocidad de antes

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        k = SS * 0.6 * self.escala
        esp = self.dir == -1
        params = [(1 - math.cos(2 * math.pi * f / 11)) / 2 for f in range(12)]
        pasto = _marcos(assets, "oveja", dibujar_oveja, k, params, esp)
        self.ancho = pasto[0].width
        n = rng.randint(3, 4)
        # cada oveja con su propio desplazamiento y fase de pastar, para que no vayan a la vez
        self.ovejas = [(rng.uniform(-0.09, 0.09) * W, rng.randrange(12)) for _ in range(n)]
        self.frames_oveja = pasto
        self.frames_oveja_vuelta = [im.transpose(Image.FLIP_LEFT_RIGHT) for im in pasto]
        self.perro = _marcos(assets, "perro", dibujar_perro, k * 1.1, list(range(4)), esp)
        self.perro_vuelta = [im.transpose(Image.FLIP_LEFT_RIGHT) for im in self.perro]
        self.y = (Y_CAMI - 0.01) * H  # cerca del camí, no sobre la pared de marjada
        self.duracion = int(self.SEG * fps)

    def _x_rebano(self, t):
        return self.x_lineal(t, self.ancho * 2, self.SEG)

    def _x_perro(self, t):
        return self._x_rebano(t) + math.sin(t / self.fps * 1.04) * 0.12 * self.W

    def sprites(self, t):
        xb = self._x_rebano(t)
        frames_oveja = self.frames_oveja_vuelta if self._saliendo else self.frames_oveja
        out = []
        for off, fase in self.ovejas:
            im = frames_oveja[(t // 4 + fase) % len(frames_oveja)]
            out.append((im, int(xb + off), int(self.y - im.height)))
        perro_frames = self.perro_vuelta if self._saliendo else self.perro
        perro = perro_frames[(t // 2) % 4]
        out.append((perro, int(self._x_perro(t)), int(self.y - perro.height + 4 * self.escala)))
        return out

    def x_interes(self, t):
        return self._x_perro(t)


class Xeremiers(Evento):
    """
    Una colla de xeremiers: dos músicos (xeremier y flabiolaire) y una
    parella de ball de bot. Entran por un lado, se acercan solo hasta un
    50% del ancho de pantalla, se quedan un rato tocando y bailando, y
    vuelven por donde han venido. Músicos y bailadors van cada uno en su
    propio grupo apretado, con un hueco claro entre los dos grupos.
    """
    capa = "fondo"
    SEG_ENTRA, SEG_TOCA, SEG_SALE = 4.0, 9.0, 4.0

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        k = SS * 0.65 * self.escala
        esp = self.dir == -1
        self.xeremier = _marcos(assets, "xeremier", dibujar_xeremier, k, list(range(4)), esp)
        self.fabioler = _marcos(assets, "fabioler", dibujar_fabioler, k, list(range(4)), esp)
        self.payes = _marcos(assets, "payes_baila", dibujar_payes_baila, k, list(range(4)), esp)
        self.payesa = _marcos(assets, "payesa_baila", dibujar_payesa_baila, k, list(range(4)), esp)

        self.y = (Y_CAMI - 0.02) * H
        ancho_grupo = 0.22 * W
        alcance = 0.5 * W
        # músicos por delante en el sentido de la marcha, bailadors detrás;
        # apretados dentro de cada grupo, con hueco claro entre ambos
        signo = 1 if self.dir == 1 else -1
        self.offsets = [
            (self.xeremier, signo * 10, 0, "paso"),
            (self.fabioler, signo * 50, 0, "paso"),
            (self.payes, signo * -70, -10, "fase"),
            (self.payesa, signo * -30, -10, "fase"),
        ]
        self.x_fuera = -ancho_grupo if self.dir == 1 else W + ancho_grupo
        self.x_dentro = alcance if self.dir == 1 else W - alcance

        self.f_entra = self.SEG_ENTRA * fps
        self.f_toca = self.f_entra + self.SEG_TOCA * fps
        self.duracion = int(self.f_toca + self.SEG_SALE * fps)

    @staticmethod
    def _suave(p):
        return p * p * (3 - 2 * p)

    def _x_grupo(self, t):
        if t < self.f_entra:
            p = self._suave(t / self.f_entra)
            return self.x_fuera + p * (self.x_dentro - self.x_fuera)
        if t < self.f_toca:
            return self.x_dentro
        p = self._suave((t - self.f_toca) / (self.duracion - self.f_toca))
        return self.x_dentro + p * (self.x_fuera - self.x_dentro)

    def sprites(self, t):
        cx = self._x_grupo(t)
        caminando = t < self.f_entra or t >= self.f_toca
        paso = (t // 4) % 4 if caminando else 0  # quietos: piernas paradas, no marcando el paso
        fase = (t // 5) % 4
        out = []
        for frames, dx, dy, anim in self.offsets:
            im = frames[paso if anim == "paso" else fase]
            out.append((im, int(cx + dx - im.width / 2), int(self.y + dy - im.height)))
        return out

    def x_interes(self, t):
        return self._x_grupo(t)


class Bronca(Evento):
    """
    Al pagès li criden des de casa: surt per la porta i es queda plantat a
    fora, mentre la seva dona l'esbronca des de la finestra amb un pal
    alçat. Luego entran los dos, él primero. Es "solapable": puede verse a
    la vez que el evento normal de turno (tractor, ovejas...), no le hace
    falta un hueco propio en la agenda principal.
    """
    capa = "fondo"
    SEG_POP = 0.4
    SEG_PAYES_FUERA = 5.0
    SEG_PAYESA_RETRASO = 0.8
    SEG_PAYESA_DURA = 4.0

    def __init__(self, W, H, fps, rng, assets=None):
        super().__init__(W, H, fps, rng, assets)
        k = SS * 0.22 * self.escala  # pequeños: son figuras lejanas junto a una casa de dos plantas
        self.payes = _marcos(assets, "payes_dret", dibujar_payes_dret, k, [-2, 0, 2, 0], False)
        self.payesa = _marcos(assets, "payesa_ventana", dibujar_payesa_ventana, k, [a / 3 for a in range(4)], False)

        base = 0.485 * H
        cx = 0.5 * W
        self.x_puerta, self.y_puerta = cx - 0.01 * W, base
        self.x_ventana, self.y_ventana = cx, (base - 0.10 * H) + 0.024 * H

        self.f_payes_entra = int(self.SEG_POP * fps)
        self.f_payes_sale = self.f_payes_entra + int(self.SEG_PAYES_FUERA * fps)
        self.f_payes_fin = self.f_payes_sale + int(self.SEG_POP * fps)

        self.f_payesa_ini = self.f_payes_entra + int(self.SEG_PAYESA_RETRASO * fps)
        self.f_payesa_fin = min(self.f_payesa_ini + int(self.SEG_PAYESA_DURA * fps), self.f_payes_fin)
        self.f_pop = int(self.SEG_POP * fps)

        self.duracion = self.f_payes_fin

    @staticmethod
    def _con_alpha(img, factor):
        if factor >= 0.999:
            return img
        im2 = img.copy()
        im2.putalpha(im2.getchannel("A").point(lambda v: int(v * factor)))
        return im2

    def _factor_payes(self, t):
        if t < self.f_payes_entra:
            return t / max(self.f_payes_entra, 1)
        if t < self.f_payes_sale:
            return 1.0
        if t < self.f_payes_fin:
            return 1.0 - (t - self.f_payes_sale) / max(self.f_payes_fin - self.f_payes_sale, 1)
        return 0.0

    def _factor_payesa(self, t):
        if t < self.f_payesa_ini or t >= self.f_payesa_fin:
            return 0.0
        d = t - self.f_payesa_ini
        if d < self.f_pop:
            return d / max(self.f_pop, 1)
        restante = self.f_payesa_fin - t
        if restante < self.f_pop:
            return restante / max(self.f_pop, 1)
        return 1.0

    def sprites(self, t):
        out = []
        fp = self._factor_payes(t)
        if fp > 0.02:
            im = self._con_alpha(self.payes[(t // 6) % len(self.payes)], fp)
            out.append((im, int(self.x_puerta - im.width / 2), int(self.y_puerta - im.height)))
        fa = self._factor_payesa(t)
        if fa > 0.02:
            im = self._con_alpha(self.payesa[(t // 4) % len(self.payesa)], fa)
            out.append((im, int(self.x_ventana - im.width / 2), int(self.y_ventana - im.height / 2)))
        return out

    def x_interes(self, t):
        if self._factor_payesa(t) > 0.3:
            return self.x_ventana
        if self._factor_payes(t) > 0.3:
            return self.x_puerta
        return None


TIPOS = {"tractor": Tractor, "cerdo": Cerdo, "pajaros": Pajaros, "gusano": Gusano, "ovejas": Ovejas,
         "xeremiers": Xeremiers, "mosquito": Mosquito, "bronca": Bronca}

# frecuencia relativa de cada tipo al elegir el siguiente evento (por defecto 1)
PESOS = {"mosquito": 3}

# tipos que no necesitan un hueco propio en la agenda principal: se programan
# en su propia línea de tiempo y pueden coincidir con cualquier otro evento
SOLAPABLES = {"bronca"}


def programar_eventos(n_frames, fps, W, H, tipos, cada, semilla, assets=None):
    """
    Devuelve una lista de (inicio, evento). Un evento cada `cada` segundos de media
    (±40 % al azar), sin repetir el mismo tipo dos veces seguidas.
    """
    if not tipos or cada <= 0:
        return []
    rng = random.Random(semilla)
    lista = []
    t = int(rng.uniform(0.4, 1.0) * cada * fps)
    anterior = None
    while t < n_frames:
        opciones = [x for x in tipos if x != anterior] or tipos
        pesos = [PESOS.get(x, 1) for x in opciones]
        tipo = rng.choices(opciones, weights=pesos)[0]
        ev = TIPOS[tipo](W, H, fps, rng, assets)
        if t + ev.duracion > n_frames:
            break
        lista.append((t, ev))
        anterior = tipo
        t += ev.duracion + int(rng.uniform(0.6, 1.4) * cada * fps)
    return lista
