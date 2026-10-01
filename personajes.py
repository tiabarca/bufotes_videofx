"""Personajes: las dos ranas (dibujadas por código o cargadas desde PNG)."""

import os

from PIL import Image, ImageDraw

#   0 cerrada · 1 vocal pequeña redonda · 2 vocal pequeña ancha
#   3 vocal grande redonda · 4 vocal grande ancha · 5 oclusiva · 6 grito
GEOM_BOCA = {
    1: (130, 230, 26),
    2: (105, 255, 22),
    3: (120, 240, 60),
    4: (95, 265, 50),
    6: (100, 260, 95),
}


def rana_generada(color, boca, ojos_abiertos, escala=1.0, mirando=1, accesorio=None):
    """
    Dibuja una rana. boca: 0-6 (ver GEOM_BOCA), ojos_abiertos: bool,
    mirando: 1 derecha / -1 izquierda, accesorio: None, "sombrero" o "gafas".
    """
    OY = 120  # margen superior (unidades de diseño) para que quepa el sombrero
    S = int(360 * escala)
    k = S / 360
    img = Image.new("RGBA", (S, int((360 + OY) * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base = tuple(color)
    oscuro = tuple(max(0, c - 45) for c in color)
    barriga = tuple(min(255, c + 70) for c in color)

    def e(x0, y0, x1, y1, dr=None, **kw):
        (dr or d).ellipse([x0 * k, (y0 + OY) * k, x1 * k, (y1 + OY) * k], **kw)

    def rect(x0, y0, x1, y1, dr=None, **kw):
        (dr or d).rounded_rectangle([x0 * k, (y0 + OY) * k, x1 * k, (y1 + OY) * k], **kw)

    def linea(pts, dr=None, **kw):
        (dr or d).line([(x * k, (y + OY) * k) for x, y in pts], **kw)

    # patas
    e(40, 270, 150, 330, fill=oscuro)
    e(210, 270, 320, 330, fill=oscuro)
    # cuerpo
    e(55, 130, 305, 320, fill=base, outline=oscuro, width=int(4 * k))
    e(105, 200, 255, 315, fill=barriga)
    # cabeza
    e(50, 90, 310, 240, fill=base, outline=oscuro, width=int(4 * k))

    # sombrero de copa, achatado (la mitad de alto que una copa normal) y
    # subido para que quede detrás/por encima de los ojos, no montado encima
    if accesorio == "sombrero":
        capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dc = ImageDraw.Draw(capa)
        negro, cinta = (35, 30, 40), (170, 45, 55)
        rect(122, -40, 238, 22, dr=dc, radius=int(10 * k), fill=negro)
        rect(122, 4, 238, 17, dr=dc, radius=int(3 * k), fill=cinta)
        e(80, 4, 280, 40, dr=dc, fill=negro)
        e(128, -45, 232, -35, dr=dc, fill=(55, 50, 62))
        capa = capa.rotate(-8 * mirando, resample=Image.BICUBIC,
                           center=(180 * k, (22 + OY) * k))
        img.alpha_composite(capa)
        d = ImageDraw.Draw(img)

    # ojos (desplazados hacia donde mira)
    dx = 10 * mirando
    for cx in (110, 250):
        e(cx - 45, 45, cx + 45, 135, fill=base, outline=oscuro, width=int(4 * k))
        if ojos_abiertos:
            e(cx - 30, 60, cx + 30, 120, fill=(255, 255, 255))
            e(cx - 13 + dx, 75, cx + 13 + dx, 105, fill=(20, 20, 20))
            e(cx - 6 + dx, 78, cx + 1 + dx, 86, fill=(255, 255, 255))
        else:
            linea([(cx - 28, 92), (cx + 28, 92)], fill=(20, 40, 20), width=int(6 * k))

    # gafas redondas con cristal tintado (capa aparte para que el tinte sea translúcido)
    if accesorio == "gafas":
        capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dc = ImageDraw.Draw(capa)
        montura = (45, 35, 30, 255)
        for cx in (110, 250):
            e(cx - 40, 50, cx + 40, 130, dr=dc, fill=(170, 210, 235, 70),
              outline=montura, width=int(8 * k))
            e(cx - 26, 60, cx - 12, 72, dr=dc, fill=(255, 255, 255, 150))  # brillo
        linea([(150, 88), (180, 80), (210, 88)], dr=dc, fill=montura, width=int(8 * k))
        linea([(70, 88), (52, 100)], dr=dc, fill=montura, width=int(7 * k))
        linea([(290, 88), (308, 100)], dr=dc, fill=montura, width=int(7 * k))
        img.alpha_composite(capa)
        d = ImageDraw.Draw(img)

    # mejillas
    e(70, 175, 105, 195, fill=(235, 140, 140))
    e(255, 175, 290, 195, fill=(235, 140, 140))
    # boca
    if boca == 0:
        d.arc([100 * k, (140 + OY) * k, 260 * k, (205 + OY) * k], 20, 160,
              fill=(30, 50, 30), width=int(6 * k))
    elif boca == 5:  # oclusiva: labios apretados y tensos
        rect(118, 178, 242, 198, fill=(120, 30, 40), outline=(30, 50, 30), width=int(4 * k))
        linea([(126, 188), (234, 188)], fill=(70, 15, 20), width=int(3 * k))
    else:
        x0, x1, alto = GEOM_BOCA[boca]
        cx = (x0 + x1) / 2
        e(x0, 170, x1, 170 + alto, fill=(120, 30, 40), outline=(30, 50, 30), width=int(5 * k))
        e(cx - 30, 170 + alto * 0.45, cx + 30, 170 + alto * 0.95, fill=(230, 110, 120))
    return img


MIRADAS = (-1, 0, 1)  # izquierda, al frente, derecha

# si no hay un PNG propio para un estado de boca nuevo (3,4,5,6), se usa el
# más parecido de los clásicos 0/1/2 para no obligar a redibujar los assets
ALTERNATIVA_BOCA = {3: 2, 4: 2, 5: 1, 6: 2}


def _ruta_boca(assets, nombre, boca):
    ruta = os.path.join(assets, f"rana{nombre}_boca{boca}.png")
    if os.path.exists(ruta):
        return ruta
    return os.path.join(assets, f"rana{nombre}_boca{ALTERNATIVA_BOCA.get(boca, 2)}.png")


def cargar_sprites(assets, colores, escala, accesorios=("sombrero", "gafas")):
    """
    Devuelve sprites[rana][(boca, ojos_abiertos, mirada)] -> RGBA.

    Con --assets usa rana{A,B}_boca{0,1,2}.png y rana{A,B}_ojos_cerrados.png
    (capa transparente que se superpone). Los PNG propios no cambian la mirada.
    Opcionalmente puedes añadir boca3.png..boca6.png (ver GEOM_BOCA); si no
    existen, se reutiliza el PNG clásico más parecido.
    """
    sprites = {}
    for r, nombre in enumerate("AB"):
        sprites[r] = {}
        for boca in (0, 1, 2, 3, 4, 5, 6):
            for ojos in (True, False):
                if assets:
                    im = Image.open(_ruta_boca(assets, nombre, boca)).convert("RGBA")
                    if not ojos:
                        pc = os.path.join(assets, f"rana{nombre}_ojos_cerrados.png")
                        if os.path.exists(pc):
                            im = Image.alpha_composite(im, Image.open(pc).convert("RGBA").resize(im.size))
                    if escala != 1.0:
                        im = im.resize((int(im.width * escala), int(im.height * escala)), Image.LANCZOS)
                    for m in MIRADAS:
                        sprites[r][(boca, ojos, m)] = im
                else:
                    for m in MIRADAS:
                        sprites[r][(boca, ojos, m)] = rana_generada(
                            colores[r], boca, ojos, escala, m, accesorios[r])
    return sprites
