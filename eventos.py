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

from escena import Y_CAMI, Y_FRENTE

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


def dibujar_cerdo(k, paso, hocica=0.0):
    """Porc negre mallorquí. paso 0..3 para las patas, hocica 0..1 baja el morro. Mira a la derecha."""
    w, h = int(210 * k), int(140 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    negro, gris, rosa = (38, 34, 38), (70, 64, 70), (150, 110, 120)

    def E(x0, y0, x1, y1, **kw):
        d.ellipse([x0 * k, y0 * k, x1 * k, y1 * k], **kw)

    # patas: pares opuestos avanzan alternos
    osc = [0, 10, 0, -10][paso % 4]
    for i, (px, fase) in enumerate(((50, 1), (72, -1), (130, -1), (152, 1))):
        dx = osc * fase
        d.polygon([((px - 7) * k, 95 * k), ((px + 7) * k, 95 * k), ((px + 5 + dx) * k, 128 * k),
                   ((px - 5 + dx) * k, 128 * k)], fill=negro if i % 2 else gris)
        E(px - 7 + dx, 122, px + 7 + dx, 132, fill=(30, 26, 28))
    # cola rizada
    d.arc([14 * k, 42 * k, 34 * k, 62 * k], 90, 400, fill=negro, width=max(1, int(4 * k)))
    # cuerpo
    E(24, 34, 176, 112, fill=negro)
    E(40, 40, 120, 70, fill=gris)  # brillo del lomo
    # cabeza (baja al hozar)
    dy = 18 * hocica
    E(138, 30 + dy, 196, 88 + dy, fill=negro)
    d.polygon([(150 * k, (34 + dy) * k), (164 * k, (8 + dy) * k), (174 * k, (38 + dy) * k)], fill=gris)  # oreja
    E(178, 56 + dy, 206, 80 + dy, fill=rosa)  # hocico
    E(186, 63 + dy, 191, 70 + dy, fill=(60, 40, 45))
    E(195, 63 + dy, 200, 70 + dy, fill=(60, 40, 45))
    E(166, 46 + dy, 174, 54 + dy, fill=(245, 245, 245))
    E(168, 48 + dy, 173, 53 + dy, fill=(10, 10, 10))
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
    capa = "frente"
    SEG = 16

    def __init__(self, W, H, fps, rng):
        super().__init__(W, H, fps, rng)
        k = SS * 0.75 * self.escala
        esp = self.dir == -1
        self.andar = [_reducir(dibujar_cerdo(k, p), esp) for p in range(4)]
        self.hozar = [_reducir(dibujar_cerdo(k, 0, h / 3), esp) for h in range(4)]
        self.ancho = self.andar[0].width
        # se para a husmear en algún punto del recorrido
        self.parada_ini = rng.uniform(0.3, 0.6)
        self.parada_seg = rng.uniform(2.0, 3.5)
        self.duracion = int((self.SEG + self.parada_seg) * fps)

    def _estado(self, t):
        s = t / self.fps
        ini = self.parada_ini * self.SEG
        if s < ini:
            return s, False
        if s < ini + self.parada_seg:
            return ini, True
        return s - self.parada_seg, False

    def _x(self, t):
        s, _ = self._estado(t)
        return self.x_lineal(s * self.fps, self.ancho, self.SEG)

    def sprites(self, t):
        s, parado = self._estado(t)
        x = self._x(t)
        if parado:
            im = self.hozar[int(abs(math.sin(t * 0.35)) * 3.99)]
            bote = 0
        else:
            im = self.andar[(t // 3) % 4]
            bote = int(abs(math.sin(t * 0.52)) * 3 * self.escala)
        y = int((Y_FRENTE + 0.01) * self.H) - im.height - bote
        return [(im, int(x), y)]

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
    capa = "frente"
    SEG = 20

    def __init__(self, W, H, fps, rng):
        super().__init__(W, H, fps, rng)
        esp = self.dir == -1
        self.frames = [_reducir(dibujar_gusano(SS * 0.6 * self.escala, i / 16), esp) for i in range(16)]
        self.ancho = self.frames[0].width
        self.duracion = int(self.SEG * fps)

    def sprites(self, t):
        x = self.x_lineal(t, self.ancho, self.SEG)
        im = self.frames[(t // 2) % 16]
        return [(im, int(x), int(Y_FRENTE * self.H) - im.height)]

    def x_interes(self, t):
        return self.x_lineal(t, self.ancho, self.SEG) + self.ancho / 2


TIPOS = {"tractor": Tractor, "cerdo": Cerdo, "pajaros": Pajaros, "gusano": Gusano}


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
