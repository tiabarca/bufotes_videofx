"""
Escena de fondo: Serra de Tramuntana con una possessió, marjades con olivos,
camí de tierra y el estanque de las ranas.

Todo se dibuja a doble resolución y se reduce al final para que los bordes
queden suaves. Las coordenadas se expresan como fracción del ancho/alto.

Posiciones que usan otros módulos (fracción del alto):
    Y_CAMI      línea por donde pasa el tractor
    Y_FRENTE    franja delantera por donde se arrastran el gusano y el cerdo
    X_RANAS     centro horizontal de cada rana (fracción del ancho)
"""

import math
import random

from PIL import Image, ImageDraw, ImageFilter

Y_CAMI = 0.555
Y_FRENTE = 0.975
X_RANAS = (0.25, 0.75)   # centro de cada rana / nenúfar

SS = 2  # supersampling


def _perfil(n, rng, rugosidad=0.55, semillas=None):
    """Perfil de cresta por desplazamiento de punto medio (valores 0..1)."""
    pts = semillas or [rng.random(), rng.random()]
    amp = 1.0
    while len(pts) < n:
        nuevo = []
        for a, b in zip(pts, pts[1:]):
            nuevo += [a, (a + b) / 2 + rng.uniform(-amp, amp) * 0.5]
        nuevo.append(pts[-1])
        pts = nuevo
        amp *= rugosidad
    mn, mx = min(pts), max(pts)
    return [(p - mn) / (mx - mn + 1e-9) for p in pts]


def _montanas(img, d, W, H, rng):
    # capa lejana: caliza azulada con el pico alto (tipo Puig Major)
    perfil = _perfil(257, rng, 0.52, [0.2, 0.5, 1.0, 0.7, 0.35, 0.6, 0.25])
    top, base = 0.11, 0.30
    pts = [(i / (len(perfil) - 1) * W, (base - (base - top) * p) * H) for i, p in enumerate(perfil)]
    poligono = pts + [(W, 0.55 * H), (0, 0.55 * H)]
    # la montaña se pinta en una capa aparte y se recorta con su silueta,
    # así las paredes de roca clara nunca se salen al cielo
    capa = Image.new("RGB", (W, H), (152, 164, 186))
    dc = ImageDraw.Draw(capa)
    for _ in range(70):
        i = rng.randrange(4, len(pts) - 4)
        x, y = pts[i]
        w = rng.uniform(0.006, 0.018) * W
        h = rng.uniform(0.04, 0.12) * H
        c = rng.choice([(172, 181, 199), (164, 174, 194), (140, 152, 176)])
        dc.polygon([(x - w, y - 4 * SS), (x + w * 0.5, y - 4 * SS), (x + w * 0.9, y + h),
                    (x - w * 0.5, y + h * 0.85)], fill=c)
    mascara = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mascara).polygon(poligono, fill=255)
    img.paste(capa, (0, 0), mascara)
    # capa media: laderas con pinar
    perfil2 = _perfil(129, rng, 0.5, [0.3, 0.8, 0.5, 0.9, 0.4])
    top2, base2 = 0.25, 0.40
    pts2 = [(i / (len(perfil2) - 1) * W, (base2 - (base2 - top2) * p) * H) for i, p in enumerate(perfil2)]
    d.polygon(pts2 + [(W, 0.6 * H), (0, 0.6 * H)], fill=(108, 128, 104))
    for _ in range(900):
        x = rng.uniform(0, W)
        i = min(int(x / W * (len(pts2) - 1)), len(pts2) - 1)
        ytop = pts2[i][1]
        y = rng.uniform(ytop + 0.01 * H, 0.47 * H)
        r = rng.uniform(0.004, 0.009) * W
        c = rng.choice([(62, 92, 58), (72, 102, 62), (55, 82, 52)])
        d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=c)


def _olivo(d, x, y, s, rng):
    tronco = (92, 72, 55)
    d.polygon([(x - s * 0.12, y), (x + s * 0.12, y), (x + s * 0.05, y - s * 0.55),
               (x + s * 0.2, y - s * 0.8), (x - s * 0.15, y - s * 0.6)], fill=tronco)
    for _ in range(6):
        dx, dy = rng.uniform(-0.6, 0.6) * s, rng.uniform(-1.25, -0.75) * s
        r = rng.uniform(0.3, 0.45) * s
        c = rng.choice([(128, 142, 104), (116, 132, 96), (140, 152, 114)])
        d.ellipse([x + dx - r, y + dy - r * 0.75, x + dx + r, y + dy + r * 0.75], fill=c)


def _marjades(d, W, H, rng):
    """Bancales de piedra seca con olivos, a ambos lados de la possessió."""
    y0, y1 = 0.38, 0.53
    d.rectangle([0, y0 * H, W, 0.6 * H], fill=(150, 158, 96))
    filas = 6
    for f in range(filas):
        y = (y0 + (y1 - y0) * f / filas) * H
        curva = [(x, y + math.sin(x / W * 5 + f) * 0.008 * H) for x in range(0, W + 20, 20)]
        franja = curva + [(W, y + 0.012 * H), (0, y + 0.012 * H)]
        d.polygon(franja, fill=(176, 160, 128))  # muro de marjada
        for x in range(0, W, int(0.012 * W)):
            yy = y + math.sin(x / W * 5 + f) * 0.008 * H
            d.line([(x, yy + 0.004 * H), (x + 0.008 * W, yy + 0.004 * H)], fill=(150, 134, 104), width=SS)
        s = (0.018 + 0.006 * f / filas) * H
        x = rng.uniform(0, 0.04) * W
        while x < W:
            if not 0.34 * W < x < 0.66 * W:  # dejar libre la possessió
                _olivo(d, x, y - 0.002 * H, s, rng)
            x += rng.uniform(0.045, 0.08) * W


def _xiprer(d, x, y, h):
    d.ellipse([x - h * 0.09, y - h, x + h * 0.09, y], fill=(40, 70, 45))
    d.ellipse([x - h * 0.05, y - h * 0.95, x + h * 0.03, y - h * 0.2], fill=(52, 84, 55))


def _palmera(d, x, y, h):
    tronco = (120, 95, 70)
    for i in range(12):
        t0, t1 = i / 12, (i + 1) / 12
        xa = x + math.sin(t0 * 1.6) * h * 0.08
        xb = x + math.sin(t1 * 1.6) * h * 0.08
        d.line([(xa, y - h * t0), (xb, y - h * t1)], fill=tronco, width=int(h * 0.045))
    cx, cy = x + math.sin(1.6) * h * 0.08, y - h
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        l = h * 0.38
        ex, ey = cx + math.cos(a) * l, cy + math.sin(a) * l * 0.55 + l * 0.25
        mx, my = cx + math.cos(a) * l * 0.5, cy + math.sin(a) * l * 0.3 - l * 0.12
        d.line([(cx, cy), (mx, my), (ex, ey)], fill=(70, 120, 60), width=int(h * 0.03), joint="curve")


def _muro_piedra(d, x0, y0, x1, y1, base, rng, junta=None):
    d.rectangle([x0, y0, x1, y1], fill=base)
    junta = junta or tuple(max(0, c - 28) for c in base)
    fila_h = max(6 * SS, (y1 - y0) / 14)
    y = y0
    fila = 0
    while y < y1:
        x = x0 - (fila % 2) * fila_h
        while x < x1:
            w = fila_h * rng.uniform(1.4, 2.4)
            c = tuple(min(255, max(0, v + rng.randint(-10, 10))) for v in base)
            ra, rb = max(x0, x) + SS, min(x1, x + w) - SS
            rc, rd = y + SS, min(y1, y + fila_h) - SS
            if rb > ra and rd > rc:
                d.rectangle([ra, rc, rb, rd], fill=c)
            x += w
        d.line([(x0, y), (x1, y)], fill=junta, width=SS)
        y += fila_h
        fila += 1


def _finestra(d, x, y, w, h, abierta):
    verde, oscuro = (62, 112, 72), (35, 30, 28)
    d.rectangle([x - w * 0.12, y - h * 0.08, x + w * 1.12, y + h * 1.06], fill=(222, 206, 170))  # marco
    if abierta:
        d.rectangle([x, y, x + w, y + h], fill=oscuro)
        d.rectangle([x - w * 0.55, y, x - w * 0.08, y + h], fill=verde)
        d.rectangle([x + w * 1.08, y, x + w * 1.55, y + h], fill=verde)
    else:
        d.rectangle([x, y, x + w, y + h], fill=verde)
        d.line([(x + w / 2, y), (x + w / 2, y + h)], fill=(40, 80, 50), width=SS)
        for k in range(1, 6):
            d.line([(x, y + h * k / 6), (x + w, y + h * k / 6)], fill=(50, 95, 60), width=SS)


def _possessio(d, W, H, rng):
    """Possessió mallorquina: casa de marès, torre de defensa, portal rodó y persianes verdes."""
    pedra = (206, 182, 142)
    teula = (172, 86, 56)
    base = 0.485 * H
    cx = 0.5 * W

    # ala baja (cases de pagès) a la derecha
    ax0, ax1 = cx + 0.045 * W, cx + 0.13 * W
    atop = base - 0.055 * H
    _muro_piedra(d, ax0, atop, ax1, base, (196, 172, 134), rng)
    d.polygon([(ax0 - 0.006 * W, atop), (ax1 + 0.006 * W, atop), (ax1, atop - 0.022 * H), (ax0, atop - 0.022 * H)],
              fill=(160, 80, 52))
    _finestra(d, ax0 + 0.025 * W, atop + 0.018 * H, 0.012 * W, 0.018 * H, True)
    d.rectangle([ax1 - 0.03 * W, base - 0.03 * H, ax1 - 0.015 * W, base], fill=(100, 62, 38))

    # casa principal
    x0, x1 = cx - 0.075 * W, cx + 0.06 * W
    top = base - 0.10 * H
    _muro_piedra(d, x0, top, x1, base, pedra, rng)
    d.polygon([(x0 - 0.01 * W, top), (x1 + 0.01 * W, top), (x1 - 0.005 * W, top - 0.03 * H),
               (x0 + 0.005 * W, top - 0.03 * H)], fill=teula)
    for i in range(12):  # canales de teja
        xx = x0 + (x1 - x0) * (i + 0.5) / 12
        d.line([(xx, top - 0.028 * H), (xx, top)], fill=(150, 72, 46), width=SS)
    d.line([(x0 - 0.01 * W, top), (x1 + 0.01 * W, top)], fill=(236, 226, 205), width=3 * SS)  # ràfec
    # ventanas
    fw, fh = 0.012 * W, 0.02 * H
    for i, fx in enumerate((x0 + 0.02 * W, cx - 0.006 * W, x1 - 0.032 * W)):
        _finestra(d, fx, top + 0.014 * H, fw, fh, abierta=(i == 1))
    # portal rodó con dovelas
    pw = 0.03 * W
    ph = 0.05 * H
    px0 = cx - pw / 2 - 0.01 * W
    d.rectangle([px0, base - ph + pw / 2, px0 + pw, base], fill=(96, 60, 36))
    d.pieslice([px0, base - ph, px0 + pw, base - ph + pw], 180, 360, fill=(96, 60, 36))
    for k in range(9):
        a = math.radians(180 + k * 22.5)
        r0, r1 = pw / 2, pw / 2 + 0.006 * W
        ccx, ccy = px0 + pw / 2, base - ph + pw / 2
        d.line([(ccx + math.cos(a) * r0, ccy + math.sin(a) * r0),
                (ccx + math.cos(a) * r1, ccy + math.sin(a) * r1)], fill=(170, 146, 110), width=SS * 2)
    d.arc([px0 - 0.006 * W, base - ph - 0.006 * W, px0 + pw + 0.006 * W, base - ph + pw + 0.006 * W],
          180, 360, fill=(170, 146, 110), width=SS * 2)

    # torre de defensa a la izquierda, con merlets
    tx0, tx1 = x0 - 0.045 * W, x0 + 0.005 * W
    ttop = base - 0.165 * H
    _muro_piedra(d, tx0, ttop, tx1, base, (198, 174, 136), rng)
    mw = (tx1 - tx0) / 7
    for k in range(0, 7, 2):
        d.rectangle([tx0 + k * mw, ttop - 0.012 * H, tx0 + (k + 1) * mw, ttop], fill=(198, 174, 136))
    d.rectangle([tx0 - 0.002 * W, ttop - 0.001 * H, tx1 + 0.002 * W, ttop + 0.004 * H], fill=(180, 156, 120))
    d.rectangle([tx0 + 0.018 * W, ttop + 0.03 * H, tx0 + 0.028 * W, ttop + 0.05 * H], fill=(40, 34, 30))
    d.pieslice([tx0 + 0.018 * W, ttop + 0.025 * H, tx0 + 0.028 * W, ttop + 0.036 * H], 180, 360,
               fill=(40, 34, 30))

    # vegetación de la casa
    _xiprer(d, tx0 - 0.015 * W, base + 0.004 * H, 0.12 * H)
    _xiprer(d, tx0 - 0.03 * W, base + 0.004 * H, 0.09 * H)
    _palmera(d, ax1 + 0.02 * W, base + 0.004 * H, 0.15 * H)


def _paret_seca(d, W, y, h, rng):
    """Muro de piedra seca de piedras irregulares."""
    x = 0.0
    while x < W:
        w = rng.uniform(0.012, 0.024) * W
        hh = h * rng.uniform(0.45, 0.6)
        for fila in (0, 1):
            yy = y + fila * h * 0.5
            c = rng.choice([(176, 168, 150), (160, 152, 136), (190, 180, 160)])
            d.rounded_rectangle([x + fila * w * 0.4, yy, x + fila * w * 0.4 + w, yy + hh],
                                radius=int(hh * 0.4), fill=c, outline=(120, 112, 98), width=SS)
        x += w * 0.92


def fondo_mallorquin(W_out, H_out, semilla=11):
    rng = random.Random(semilla)
    W, H = W_out * SS, H_out * SS
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)

    # cielo mediterráneo
    for y in range(int(H * 0.6)):
        t = y / (H * 0.6)
        d.line([(0, y), (W, y)], fill=(int(118 + 110 * t), int(178 + 60 * t), int(228 + 12 * t)))
    _montanas(img, d, W, H, rng)
    _marjades(d, W, H, rng)
    _possessio(d, W, H, rng)

    # campo seco y camí de tierra
    d.rectangle([0, 0.485 * H, W, H], fill=(186, 176, 104))
    for _ in range(1400):
        x, y = rng.uniform(0, W), rng.uniform(0.49, 0.72) * H
        d.line([(x, y), (x + rng.uniform(-3, 3) * SS, y - rng.uniform(4, 10) * SS)],
               fill=rng.choice([(160, 150, 80), (200, 188, 120), (146, 150, 78)]), width=SS)
    _paret_seca(d, W, 0.49 * H, 0.03 * H, rng)
    d.polygon([(0, (Y_CAMI - 0.018) * H), (W, (Y_CAMI - 0.022) * H), (W, (Y_CAMI + 0.012) * H),
               (0, (Y_CAMI + 0.016) * H)], fill=(196, 160, 112))
    for _ in range(160):
        x = rng.uniform(0, W)
        y = rng.uniform(Y_CAMI - 0.015, Y_CAMI + 0.01) * H
        d.ellipse([x, y, x + 3 * SS, y + 2 * SS], fill=(170, 136, 94))
    # algún almendro suelto en el campo
    for x in (0.08, 0.93):
        _olivo(d, x * W, 0.6 * H, 0.03 * H, rng)

    # estanque
    d.ellipse([-0.12 * W, 0.68 * H, 1.12 * W, 1.45 * H], fill=(96, 118, 88))  # orilla húmeda
    d.ellipse([-0.08 * W, 0.70 * H, 1.08 * W, 1.40 * H], fill=(58, 112, 138))
    d.ellipse([0.0, 0.73 * H, 1.0 * W, 1.35 * H], fill=(68, 128, 154))
    # los nenúfares van por delante del brillo animado del agua: se dibujan
    # cada fotograma con generar_nenufares()/dibujar_nenufares(), no aquí.

    # franja delantera de tierra y piedras (por aquí pasa el gusano)
    d.polygon([(0, 0.935 * H)] + [(x, (0.94 + 0.008 * math.sin(x / W * 9)) * H) for x in range(0, W + 40, 40)]
              + [(W, H), (0, H)], fill=(128, 98, 68))
    for _ in range(90):
        x, y = rng.uniform(0, W), rng.uniform(0.945, 1.0) * H
        r = rng.uniform(3, 9) * SS
        d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=rng.choice([(168, 160, 146), (148, 140, 126)]))
    for _ in range(120):
        x = rng.uniform(0, W)
        d.line([(x, 0.945 * H), (x + rng.uniform(-6, 6) * SS, 0.945 * H - rng.uniform(6, 18) * SS)],
               fill=(96, 140, 60), width=2 * SS)

    img = img.filter(ImageFilter.SMOOTH)
    return img.resize((W_out, H_out), Image.LANCZOS)


# ----------------------------------------------------------------------------
# Elementos animados: nubes que cruzan el cielo, cañas con viento, brillo
# del agua. Se calculan en resolución final (sin supersampling): son pocos
# trazos y repintarlos cada fotograma es barato.
# ----------------------------------------------------------------------------

def _dibujar_nube(rng, escala):
    """Nube suelta en silueta blanda, lista para desplazarse por el cielo."""
    base_w, base_h = 140 * escala, 70 * escala
    # lienzo con margen de sobra: si una bola se desplaza al extremo del rango
    # (ox/r máximos) no debe tocar el borde, o se vería un corte en seco
    w, h = max(1, int(base_w * 1.5)), max(1, int(base_h * 1.4))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = w * 0.5, h * 0.5
    for _ in range(6):
        r = rng.uniform(0.16, 0.30) * base_w
        ox = rng.uniform(-0.38, 0.38) * base_w
        oy = rng.uniform(-0.12, 0.12) * base_h
        d.ellipse([cx + ox - r, cy + oy - r * 0.55, cx + ox + r, cy + oy + r * 0.55],
                  fill=(248, 250, 252, 235))
    return img


class Nubes:
    """
    Nubes que se van generando por la derecha y cruzan el cielo muy despacio
    hacia la izquierda, sin parar durante todo el vídeo (tarda varios minutos
    en cruzar la pantalla entera).
    """

    def __init__(self, n_frames, fps, W, H, semilla, cada=13.0, al_empezar=(4, 5)):
        rng = random.Random(semilla)
        self.W = W
        vel_px_seg = 0.0035 * W  # muy lento: cruza la pantalla en ~5 min
        self.agenda = []  # (frame_inicio, sprite, y, vel_px_por_frame)

        def nueva_nube():
            tam = rng.uniform(0.7, 1.6) * H / 720
            sprite = _dibujar_nube(rng, tam)
            y = rng.uniform(0.03, 0.15) * H
            vel = (vel_px_seg * rng.uniform(0.7, 1.3)) / fps
            return sprite, y, vel

        # unas cuantas ya repartidas por el cielo desde el primer fotograma,
        # en vez de empezar con el cielo vacío
        for _ in range(rng.randint(*al_empezar)):
            sprite, y, vel = nueva_nube()
            x0 = rng.uniform(-0.1, 1.0) * W
            t0 = int((x0 - self.W) / vel)
            self.agenda.append((t0, sprite, y, vel))

        t = int(rng.uniform(0.1, 1.0) * cada * fps)
        while t < n_frames:
            sprite, y, vel = nueva_nube()
            self.agenda.append((t, sprite, y, vel))
            t += int(rng.uniform(0.5, 1.6) * cada * fps)

    def sprites(self, i):
        """Lista de (imagen, x, y) a pintar en el fotograma `i`."""
        out = []
        for t0, sprite, y, vel in self.agenda:
            if i < t0:
                continue
            x = self.W - (i - t0) * vel
            if x < -sprite.width:
                continue
            out.append((sprite, int(x), int(y)))
        return out


def generar_canas(W, H, semilla):
    """Posiciones de las cañas de las esquinas del estanque (sin dibujar)."""
    rng = random.Random(semilla)
    canas = []
    for x0 in [rng.uniform(0, 0.12) for _ in range(12)] + [rng.uniform(0.88, 1.0) for _ in range(12)]:
        xb = x0 * W
        top = rng.uniform(0.5, 0.62) * H
        dx = rng.uniform(-12, 12)
        cabeza = rng.random() < 0.45
        fase = rng.uniform(0, 2 * math.pi)
        periodo = rng.uniform(2.6, 4.2)
        canas.append((xb, top, dx, cabeza, fase, periodo))
    return canas


def dibujar_canas(d, canas, t_seg, H):
    """Balanceo sutil y continuo de las cañas, como si las moviera el viento."""
    amp = 0.012 * H
    for xb, top, dx, cabeza, fase, periodo in canas:
        viento = amp * math.sin(2 * math.pi * t_seg / periodo + fase)
        tx, ty = xb + dx + viento, top
        d.line([(xb, 0.8 * H), (tx, ty)], fill=(78, 112, 52), width=3)
        if cabeza:
            d.ellipse([tx - 5, ty, tx + 5, ty + 0.05 * H], fill=(112, 76, 46))


def generar_reflejos(W, H, semilla):
    """Parámetros de los brillos del agua (orilla y reflejo de la montaña)."""
    rng = random.Random(semilla)
    reflejos = []
    for _ in range(40):
        x, y = rng.uniform(0, W), rng.uniform(0.74, 0.93) * H
        largo = rng.uniform(20, 70)
        reflejos.append((x, y, largo, (118, 172, 196), 2, rng.uniform(0, 2 * math.pi), rng.uniform(2.5, 5.0)))
    for _ in range(14):
        x, y = rng.uniform(0.2, 0.8) * W, rng.uniform(0.74, 0.8) * H
        largo = rng.uniform(30, 90)
        reflejos.append((x, y, largo, (92, 142, 166), 3, rng.uniform(0, 2 * math.pi), rng.uniform(3.0, 6.0)))
    return reflejos


def dibujar_reflejos(d, reflejos, t_seg, W):
    """Brillo del agua: vaivén horizontal muy suave y continuo (rizos de la superficie)."""
    amp = 0.012 * W
    for x, y, largo, color, ancho, fase, periodo in reflejos:
        dx = amp * math.sin(2 * math.pi * t_seg / periodo + fase)
        d.line([(x + dx, y), (x + dx + largo, y)], fill=color, width=ancho)


def _dibujar_hoja_nenufar(s, angulo, lado):
    """
    Hoja de nenúfar con su muesca característica (transparente, deja ver el
    agua de verdad a través) y un par de venas que abren desde ahí. La
    muesca se abre hacia arriba y un poco hacia `lado` (1 o -1) en vez de
    justo hacia arriba, porque si no queda tapada por la rana sentada encima.
    Se dibuja a 2x y se suaviza, igual que el resto del fondo, y se gira un
    poco: si no, al pintarse nítida cada fotograma sobre un fondo con los
    bordes suavizados parece una pegatina recortada encima.
    """
    w, h = max(1, int(s * SS)), max(1, int(s * 0.42 * SS))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    verde, sombra = (60, 140, 60), (40, 100, 40)
    d.ellipse([0, 0, w - 1, h - 1], fill=verde, outline=sombra, width=4 * SS)
    centro = 310 if lado > 0 else 230
    d.pieslice([0, 0, w - 1, h - 1], centro - 20, centro + 20, fill=(0, 0, 0, 0))
    cx, cy = w / 2, h / 2
    base = centro + 180  # las venas abren desde la muesca hacia el resto de la hoja
    for off in (-35, 0, 35):
        ang = math.radians(base + off)
        d.line([(cx, cy), (cx + math.cos(ang) * w * 0.46, cy + math.sin(ang) * h * 0.42)],
               fill=sombra, width=max(1, int(1.3 * SS)))
    img = img.filter(ImageFilter.SMOOTH)
    img = img.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    return img.rotate(angulo, resample=Image.BICUBIC, expand=True)


def _dibujar_flor_nenufar():
    """Florecita de nenúfar, suavizada igual que las hojas."""
    r = 14 * SS
    img = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for ang in range(0, 360, 45):
        ra = math.radians(ang)
        ox, oy = math.cos(ra) * 8 * SS, math.sin(ra) * 4 * SS
        d.ellipse([r + ox - 6 * SS, r + oy - 3 * SS, r + ox + 6 * SS, r + oy + 3 * SS], fill=(246, 206, 222))
    d.ellipse([r - 4 * SS, r - 3 * SS, r + 4 * SS, r + 3 * SS], fill=(240, 200, 70))
    img = img.filter(ImageFilter.SMOOTH)
    return img.resize((max(1, r * 2 // SS), max(1, r * 2 // SS)), Image.LANCZOS)


def generar_nenufares(W, H, semilla=11):
    """
    Sprites (ya suavizados y listos para pegar) de las hojas de nenúfar bajo
    cada rana y alguna flor. Las hojas se giran un poco al azar y se centran
    más arriba, con margen de sobra para no llegar a tocar la franja de
    tierra del frente (en vez de apoyar el borde superior ahí, como antes).
    """
    rng = random.Random(semilla + 500)
    nenufares = []
    for i, cx in enumerate(X_RANAS):
        s = 0.26 * W
        lado = 1 if i == 0 else -1  # la muesca mira hacia fuera de cada rana, no hacia la otra
        sprite = _dibujar_hoja_nenufar(s, rng.uniform(-8, 8), lado)
        y_centro = 0.80 * H
        nenufares.append((sprite, cx * W - sprite.width / 2, y_centro - sprite.height / 2))
    for fx, fy in ((0.5, 0.88), (0.1, 0.9), (0.9, 0.86)):
        sprite = _dibujar_flor_nenufar()
        nenufares.append((sprite, fx * W - sprite.width / 2, fy * H - sprite.height / 2))
    return nenufares


def dibujar_nenufares(img, nenufares):
    """Pega las hojas y flores de nenúfar, por delante del brillo del agua."""
    for sprite, x, y in nenufares:
        img.paste(sprite, (int(x), int(y)), sprite)


def _dibujar_microfono(escala):
    """
    Micro vintage de pie, grande y de silueta simple (pocas bandas gruesas
    en vez de una rejilla fina) para que se lea bien aunque sea pequeño en
    el vídeo: cabeza redondeada, yugo en U cromado, pie y base de peso.
    """
    k = SS * 0.9 * escala
    w, h = int(100 * k), int(190 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    gris, oscuro, cromo = (215, 215, 220), (30, 28, 30), (175, 175, 180)
    cx = 50 * k

    d.ellipse([cx - 32 * k, 168 * k, cx + 32 * k, 190 * k], fill=oscuro)   # base de peso
    d.ellipse([cx - 27 * k, 168 * k, cx + 27 * k, 185 * k], fill=gris)
    d.rectangle([cx - 5 * k, 94 * k, cx + 5 * k, 172 * k], fill=cromo)     # pie

    d.arc([cx - 22 * k, 76 * k, cx + 22 * k, 104 * k], 200, 340, fill=cromo,  # yugo en U
          width=max(1, int(6 * k)))
    d.ellipse([cx - 6 * k, 85 * k, cx + 6 * k, 97 * k], fill=oscuro)

    d.rounded_rectangle([cx - 28 * k, 18 * k, cx + 28 * k, 90 * k], radius=int(26 * k),
                         fill=gris, outline=oscuro, width=max(1, int(3 * k)))  # cabeza
    for yy in range(30, 80, 11):  # pocas bandas, gruesas
        d.rounded_rectangle([cx - 22 * k, yy * k, cx + 22 * k, (yy + 6) * k], radius=int(3 * k), fill=oscuro)

    img = img.filter(ImageFilter.SMOOTH)
    return img.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)


def generar_microfonos(W, H, y_base, escala):
    """
    Un micro vintage fijo delante de cada rana, apoyado en el nenúfar. No se
    mueve con la rana (ni con el bote ni la respiración): queda siempre en
    el mismo sitio del nenúfar, como un micro de pie de verdad.
    """
    micros = []
    for i, cx in enumerate(X_RANAS):
        sprite = _dibujar_microfono(escala)
        lado = 0.06 if i == 0 else -0.06  # algo hacia el centro, como en una entrevista
        x = cx * W + lado * W - sprite.width / 2
        y = y_base - sprite.height
        micros.append((sprite, x, y))
    return micros


def dibujar_microfonos(img, micros):
    """Pega los micrófonos, por delante de las ranas."""
    for sprite, x, y in micros:
        img.paste(sprite, (int(x), int(y)), sprite)


if __name__ == "__main__":
    fondo_mallorquin(1280, 720).save("fondo_preview.png")
    print("fondo_preview.png guardado")
