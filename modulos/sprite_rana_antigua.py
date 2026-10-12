"""
Versión antigua de las ranas (la de antes de las manchas y verrugas): dibujo
plano de óvalos, un solo tono con borde oscuro, mejillas rosas y ojos
blancos con pupila negra. Se elige con `--tiporana oldversion`.

Solo tiene postura sentada: la postura se ignora (el resto de gestos de
movimiento.py —ladeo, desplazamiento— siguen funcionando).
"""

from PIL import Image, ImageDraw

OY = 120  # margen superior (igual que personajes.OY) para que quepa el sombrero


def dibujar(color, boca, ojos_abiertos, escala=1.0, mirando=1, accesorio=None, postura=0, geom_boca=None):
    """Devuelve la rana como RGBA del mismo tamaño que personajes._lienzo(escala)."""
    from .personajes import GEOM_BOCA
    geom_boca = geom_boca or GEOM_BOCA
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

    # sombrero de copa, achatado y bajado a la altura de la cabeza (los ojos lo tapan por abajo)
    if accesorio == "sombrero":
        BAJA = 26
        capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dc = ImageDraw.Draw(capa)
        negro, cinta = (35, 30, 40), (170, 45, 55)
        rect(122, -40 + BAJA, 238, 22 + BAJA, dr=dc, radius=int(10 * k), fill=negro)
        rect(122, 4 + BAJA, 238, 17 + BAJA, dr=dc, radius=int(3 * k), fill=cinta)
        e(80, 4 + BAJA, 280, 40 + BAJA, dr=dc, fill=negro)
        e(128, -45 + BAJA, 232, -35 + BAJA, dr=dc, fill=(55, 50, 62))
        capa = capa.rotate(-8 * mirando, resample=Image.BICUBIC, center=(180 * k, (22 + BAJA + OY) * k))
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

    # gafas redondas con cristal tintado
    if accesorio == "gafas":
        capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dc = ImageDraw.Draw(capa)
        montura = (45, 35, 30, 255)
        for cx in (110, 250):
            e(cx - 40, 50, cx + 40, 130, dr=dc, fill=(170, 210, 235, 70), outline=montura, width=int(8 * k))
            e(cx - 26, 60, cx - 12, 72, dr=dc, fill=(255, 255, 255, 150))
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
        d.arc([100 * k, (140 + OY) * k, 260 * k, (205 + OY) * k], 20, 160, fill=(30, 50, 30), width=int(6 * k))
    elif boca == 5:  # oclusiva: labios apretados y tensos
        rect(118, 178, 242, 198, fill=(120, 30, 40), outline=(30, 50, 30), width=int(4 * k))
        linea([(126, 188), (234, 188)], fill=(70, 15, 20), width=int(3 * k))
    else:
        x0, x1, alto = geom_boca[boca]
        cx = (x0 + x1) / 2
        e(x0, 170, x1, 170 + alto, fill=(120, 30, 40), outline=(30, 50, 30), width=int(5 * k))
        e(cx - 30, 170 + alto * 0.45, cx + 30, 170 + alto * 0.95, fill=(230, 110, 120))
    return img
