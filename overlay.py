"""Logo del podcast (esquina superior izquierda) y título de entrada."""

import os

from PIL import Image, ImageDraw, ImageFont

RUTA_FUENTE = os.path.join(os.path.dirname(__file__), "media", "fuentes", "PermanentMarker-Regular.ttf")
RUTA_LOGO = os.path.join(os.path.dirname(__file__), "media", "logo.png")
RUTA_PORTADA = os.path.join(os.path.dirname(__file__), "media", "portada.jpeg")

# colores sacados del propio logo: amarillo del rótulo, marino del borde
AMARILLO = (247, 193, 0, 255)
MARINO = (6, 26, 48, 255)

SEG_FADE = 0.6  # entrada/salida del título, en segundos
SEG_FADE_PORTADA = 1.5  # desvanecido de la portada hacia la escena, al final de su duración


def cargar_logo(H, ruta=RUTA_LOGO, alto_rel=0.16):
    """Logo reescalado a una fracción de la altura del vídeo, o None si no existe/está desactivado."""
    if not ruta or not os.path.exists(ruta):
        return None
    im = Image.open(ruta).convert("RGBA")
    alto = int(H * alto_rel)
    ancho = int(im.width * alto / im.height)
    return im.resize((ancho, alto), Image.LANCZOS)


def cargar_portada(W, H, ruta=RUTA_PORTADA):
    """Portada tal cual (ya viene a 16:9), encajada a pantalla completa. None si no existe."""
    if not ruta or not os.path.exists(ruta):
        return None
    return Image.open(ruta).convert("RGBA").resize((W, H), Image.LANCZOS)


def factor_portada(t_seg, duracion, fade=SEG_FADE_PORTADA):
    """1 (opaca) hasta el tramo final, donde se desvanece hacia la escena en `fade` segundos."""
    if t_seg >= duracion:
        return 0.0
    if t_seg > duracion - fade:
        return max(0.0, (duracion - t_seg) / fade)
    return 1.0


def _envolver(texto, fuente, ancho_max, draw):
    """Reparte el texto en líneas que quepan en ancho_max (sin cortar palabras)."""
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        x0, _, x1, _ = draw.textbbox((0, 0), prueba, font=fuente, stroke_width=1)
        if x1 - x0 <= ancho_max or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def dibujar_titulo(texto, W, escala=1.0):
    """
    Imagen RGBA del título (ancho = W, envuelto a varias líneas si hace
    falta), en el estilo del logo: marcador amarillo con borde marino.
    Si no cabe en 2 líneas, reduce la letra hasta que quepa (mínimo 3).
    """
    tam = int(100 * escala)
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for _ in range(6):
        fuente = ImageFont.truetype(RUTA_FUENTE, tam)
        lineas = _envolver(texto, fuente, W * 0.86, tmp)
        if len(lineas) <= 2 or tam <= int(40 * escala):
            break
        tam = int(tam * 0.85)
    trazo = max(2, int(tam * 0.08))
    alto_linea = int(tam * 1.3)
    img = Image.new("RGBA", (W, alto_linea * len(lineas) + trazo * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for i, linea in enumerate(lineas):
        y = trazo + i * alto_linea
        draw.text((W / 2, y), linea, font=fuente, fill=AMARILLO,
                   stroke_width=trazo, stroke_fill=MARINO, anchor="ma")
    return img


def factor_titulo(t_seg, duracion):
    """0..1: entra y sale con un fundido de SEG_FADE segundos."""
    if t_seg < 0 or t_seg >= duracion:
        return 0.0
    if t_seg < SEG_FADE:
        return t_seg / SEG_FADE
    if t_seg > duracion - SEG_FADE:
        return (duracion - t_seg) / SEG_FADE
    return 1.0


def con_alpha(img, factor):
    """Copia de img con el canal alfa escalado por factor (0..1)."""
    if factor >= 0.999:
        return img
    im2 = img.copy()
    im2.putalpha(im2.getchannel("A").point(lambda v: int(v * factor)))
    return im2
