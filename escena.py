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
    for _ in range(5):  # nubes
        cx, cy = rng.uniform(0, W), rng.uniform(0.04, 0.13) * H
        for _ in range(6):
            r = rng.uniform(0.02, 0.04) * W
            ox = rng.uniform(-0.05, 0.05) * W
            d.ellipse([cx + ox - r, cy - r * 0.5, cx + ox + r, cy + r * 0.5], fill=(248, 250, 252))

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
    for _ in range(40):
        x, y = rng.uniform(0, W), rng.uniform(0.74, 0.93) * H
        d.line([(x, y), (x + rng.uniform(20, 70) * SS, y)], fill=(118, 172, 196), width=2 * SS)
    # reflejo de la montaña
    for _ in range(14):
        x, y = rng.uniform(0.2, 0.8) * W, rng.uniform(0.74, 0.8) * H
        d.line([(x, y), (x + rng.uniform(30, 90) * SS, y)], fill=(92, 142, 166), width=3 * SS)

    # cañas (canyes) en las esquinas
    for x0 in [rng.uniform(0, 0.12) for _ in range(12)] + [rng.uniform(0.88, 1.0) for _ in range(12)]:
        top = rng.uniform(0.5, 0.62) * H
        xb = x0 * W
        d.line([(xb, 0.8 * H), (xb + rng.uniform(-12, 12) * SS, top)], fill=(78, 112, 52), width=3 * SS)
        if rng.random() < 0.45:
            d.ellipse([xb - 5 * SS, top, xb + 5 * SS, top + 0.05 * H], fill=(112, 76, 46))

    # nenúfares bajo cada rana
    for cx in X_RANAS:
        s = 0.26 * W
        x0, y0 = cx * W - s / 2, 0.80 * H
        d.ellipse([x0, y0, x0 + s, y0 + s * 0.42], fill=(60, 140, 60), outline=(40, 100, 40), width=4 * SS)
        d.pieslice([x0, y0, x0 + s, y0 + s * 0.42], 250, 290, fill=(68, 128, 154))
    # alguna flor de nenúfar
    for fx, fy in ((0.5, 0.88), (0.1, 0.9), (0.9, 0.86)):
        x, y = fx * W, fy * H
        for a in range(0, 360, 45):
            ra = math.radians(a)
            d.ellipse([x + math.cos(ra) * 8 * SS - 6 * SS, y + math.sin(ra) * 4 * SS - 3 * SS,
                       x + math.cos(ra) * 8 * SS + 6 * SS, y + math.sin(ra) * 4 * SS + 3 * SS],
                      fill=(246, 206, 222))
        d.ellipse([x - 4 * SS, y - 3 * SS, x + 4 * SS, y + 3 * SS], fill=(240, 200, 70))

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


if __name__ == "__main__":
    fondo_mallorquin(1280, 720).save("fondo_preview.png")
    print("fondo_preview.png guardado")
