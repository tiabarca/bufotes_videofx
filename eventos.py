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
import random

from PIL import Image, ImageDraw

from escena import X_RANAS, Y_CAMI, Y_FRENTE

SS = 2  # supersampling de los sprites


def _reducir(img, espejo=False):
    img = img.resize((max(1, img.width // SS), max(1, img.height // SS)), Image.LANCZOS)
    return img.transpose(Image.FLIP_LEFT_RIGHT) if espejo else img


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


# ----------------------------------------------------------------------------
# Eventos
# ----------------------------------------------------------------------------

class Evento:
    capa = "fondo"

    def __init__(self, W, H, fps, rng):
        self.W, self.H, self.fps = W, H, fps
        self.dir = rng.choice((1, -1))  # 1: de izquierda a derecha
        self.escala = H / 720

    def x_lineal(self, t, ancho, segundos):
        """Cruza la pantalla de un lado a otro en `segundos`."""
        p = t / (segundos * self.fps)
        x = -ancho + p * (self.W + 2 * ancho)
        return x if self.dir == 1 else self.W - x - ancho

    def x_interes(self, t):
        return None


class Tractor(Evento):
    capa = "fondo"
    SEG = 13

    def __init__(self, W, H, fps, rng):
        super().__init__(W, H, fps, rng)
        k = SS * 0.55 * self.escala
        esp = self.dir == -1
        self.frames = [_reducir(dibujar_tractor(k, i / 8), esp) for i in range(8)]
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
        out = []
        esc = self.frames[0].width * (152 / 260)  # posición del tubo de escape
        ex = x + (esc if self.dir == 1 else self.frames[0].width - esc)
        for j in range(4):  # bocanadas que se quedan atrás y suben
            edad = ((t / 4 + j * 2.5) % 10)
            im = self.humo[int(edad)]
            hx = ex - self.dir * edad * 6 * self.escala - im.width / 2
            hy = y + 18 * self.escala - edad * 7 * self.escala - im.height / 2
            out.append((im, int(hx), int(hy)))
        out.append((self.frames[(t // 2) % 8], int(x), y))
        return out

    def x_interes(self, t):
        return self._pos(t)[0] + self.ancho / 2


class Cerdo(Evento):
    """El porc negre huye por el camí con una muchedumbre de payeses detrás, cuchillo y olla en alto."""
    capa = "fondo"
    SEG = 11

    def __init__(self, W, H, fps, rng):
        super().__init__(W, H, fps, rng)
        k = SS * 0.75 * self.escala
        esp = self.dir == -1
        self.cerdo = [_reducir(dibujar_cerdo_corriendo(k * 0.5, p), esp) for p in range(4)]  # el porc, la mitad de grande
        self.ancho = self.cerdo[0].width
        n = rng.randint(4, 5)  # una muchedumbre de verdad
        self.payeses = []
        retraso_base = rng.uniform(0.4, 0.55)  # que no le vayan pisando los talones al porc
        for j in range(n):
            arma = "cuchillo" if j % 2 == 0 else "olla"
            frames = [_reducir(dibujar_payes(k * 0.8, p, arma), esp) for p in range(4)]
            retraso = retraso_base + j * rng.uniform(0.14, 0.22)  # cada uno un poco más atrás, desincronizados
            dy = rng.uniform(-4, 4) * self.escala
            self.payeses.append((frames, retraso, dy))
        self.y = (Y_CAMI - 0.03) * H  # junto al camí, cerca de por donde pasa el tractor
        self.duracion = int(self.SEG * fps)

    def _x(self, t, retraso=0.0):
        return self.x_lineal(t - retraso * self.fps, self.ancho, self.SEG)

    def sprites(self, t):
        out = []
        for frames, retraso, dy in self.payeses:
            x = self._x(t, retraso)
            im = frames[(t // 3) % 4]
            out.append((im, int(x), int(self.y - im.height + dy)))
        xc = self._x(t)
        out.append((self.cerdo[(t // 2) % 4], int(xc), int(self.y - self.cerdo[0].height)))
        return out

    def x_interes(self, t):
        return self._x(t) + self.ancho / 2


class Pajaros(Evento):
    capa = "fondo"
    SEG = 9

    def __init__(self, W, H, fps, rng):
        super().__init__(W, H, fps, rng)
        esp = self.dir == -1
        self.frames = [
            [_reducir(dibujar_pajaro(SS * 1.0 * self.escala * s, 0.5 - 0.5 * math.cos(2 * math.pi * i / 8)), esp)
             for i in range(8)]
            for s in (1.0, 0.8)
        ]
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
            im = self.frames[n][(t // 2 + n * 3) % 8]
            out.append((im, int(x), int(y)))
        return out

    def x_interes(self, t):
        return self._pos(t, 0)[0] + self.ancho / 2


class Gusano(Evento):
    """Un gusano se arrastra hacia la primera rana que encuentra; al llegar, se lo come de un lengüetazo."""
    capa = "frente"
    VEL = 20  # segundos que tardaría en cruzar la pantalla entera, para mantener el mismo ritmo de antes

    def __init__(self, W, H, fps, rng):
        super().__init__(W, H, fps, rng)
        esp = self.dir == -1
        self.frames = [_reducir(dibujar_gusano(SS * 0.6 * self.escala, i / 16), esp) for i in range(16)]
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

    def sprites(self, t):
        if t < self.frame_captura:
            p = t / max(self.frame_captura, 1)
            x = self.x_inicio + p * (self.x_parada - self.x_inicio)
            im = self.frames[(t // 2) % 16]
            return [(im, int(x - self.ancho / 2), int(self.y_suelo) - im.height)]

        # lengüetazo: dispara rápido, agarra y recoge (más lento, como si cargara con la presa)
        t2 = t - self.frame_captura
        total = max(self.duracion - self.frame_captura, 1)
        p = min(t2 / total, 1.0)
        ext = p / 0.3 if p < 0.3 else max(0.0, 1 - (p - 0.3) / 0.7)
        tx = self.x_boca + (self.x_parada - self.x_boca) * ext
        ty = self.y_boca + (self.y_suelo - self.y_boca) * ext

        lengua, mx, my = self._lengua(tx, ty)
        out = [(lengua, mx, my)]
        if ext > 0.03:  # el gusano va pegado a la punta hasta que casi ha vuelto a la boca
            im = self.frames[0]
            out.append((im, int(tx - self.ancho / 2), int(ty - im.height / 2)))
        return out

    def x_interes(self, t):
        if t < self.frame_captura:
            p = t / max(self.frame_captura, 1)
            return self.x_inicio + p * (self.x_parada - self.x_inicio)
        return None

    def boca_forzada(self, t):
        """(índice_rana, estado_boca): abre un poco la boca al lanzar la lengua, cierra al tragar."""
        if t < self.frame_captura:
            return None
        t2 = t - self.frame_captura
        total = max(self.duracion - self.frame_captura, 1)
        p = min(t2 / total, 1.0)
        ext = p / 0.3 if p < 0.3 else max(0.0, 1 - (p - 0.3) / 0.7)
        return (self.objetivo, 1 if ext > 0.03 else 0)


class Ovejas(Evento):
    """Un rebaño pasturando despacio por el campo, con un perro que lo persigue de un lado a otro."""
    capa = "fondo"
    SEG = 24  # 19 / 0.8: van a un 80% de la velocidad de antes

    def __init__(self, W, H, fps, rng):
        super().__init__(W, H, fps, rng)
        k = SS * 0.6 * self.escala
        esp = self.dir == -1
        pasto = [_reducir(dibujar_oveja(k, (1 - math.cos(2 * math.pi * f / 11)) / 2), esp) for f in range(12)]
        self.ancho = pasto[0].width
        n = rng.randint(3, 4)
        # cada oveja con su propio desplazamiento y fase de pastar, para que no vayan a la vez
        self.ovejas = [(rng.uniform(-0.09, 0.09) * W, rng.randrange(12)) for _ in range(n)]
        self.frames_oveja = pasto
        self.perro = [_reducir(dibujar_perro(k * 1.1, p), esp) for p in range(4)]
        self.y = (Y_CAMI - 0.01) * H  # cerca del camí, no sobre la pared de marjada
        self.duracion = int(self.SEG * fps)

    def _x_rebano(self, t):
        return self.x_lineal(t, self.ancho * 2, self.SEG)

    def _x_perro(self, t):
        return self._x_rebano(t) + math.sin(t / self.fps * 1.04) * 0.12 * self.W

    def sprites(self, t):
        xb = self._x_rebano(t)
        out = []
        for off, fase in self.ovejas:
            im = self.frames_oveja[(t // 4 + fase) % len(self.frames_oveja)]
            out.append((im, int(xb + off), int(self.y - im.height)))
        perro = self.perro[(t // 2) % 4]
        out.append((perro, int(self._x_perro(t)), int(self.y - perro.height + 4 * self.escala)))
        return out

    def x_interes(self, t):
        return self._x_perro(t)


TIPOS = {"tractor": Tractor, "cerdo": Cerdo, "pajaros": Pajaros, "gusano": Gusano, "ovejas": Ovejas}


def programar_eventos(n_frames, fps, W, H, tipos, cada, semilla):
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
        tipo = rng.choice(opciones)
        ev = TIPOS[tipo](W, H, fps, rng)
        if t + ev.duracion > n_frames:
            break
        lista.append((t, ev))
        anterior = tipo
        t += ev.duracion + int(rng.uniform(0.6, 1.4) * cada * fps)
    return lista
