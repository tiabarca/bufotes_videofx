"""Personajes: las dos ranas (dibujadas por código o cargadas desde PNG)."""

import os

from PIL import Image

from . import sprite_rana as _sprite_rana
from . import sprite_rana_antigua as _sprite_rana_antigua

TIPOS_RANA = {"nueva": _sprite_rana, "oldversion": _sprite_rana_antigua}

#   0 cerrada · 1 vocal pequeña redonda · 2 vocal pequeña ancha
#   3 vocal grande redonda · 4 vocal grande ancha · 5 oclusiva · 6 grito
GEOM_BOCA = {
    1: (130, 230, 26),
    2: (105, 255, 22),
    3: (120, 240, 60),
    4: (95, 265, 50),
    6: (100, 260, 95),
}


OY = 120  # margen superior (unidades de diseño) para que quepa el sombrero


def _lienzo(escala):
    """Tamaño (ancho, alto) del lienzo de una rana a una escala dada, y su factor k."""
    S = int(360 * escala)
    k = S / 360
    return S, int((360 + OY) * k), k


def rana_generada(color, boca, ojos_abiertos, escala=1.0, mirando=1, accesorio=None, postura=0, tipo="nueva"):
    """
    Dibuja una rana (sapo verde balear, ver modulos/sprite_rana.py).
    boca: 0-6 (ver GEOM_BOCA), ojos_abiertos: bool, mirando: 1 derecha /
    -1 izquierda / 0 al frente, accesorio: None, "sombrero" o "gafas",
    postura: 0 sentada, 1 agachada, 2 en el aire, 3 erguida.
    tipo: "nueva" o "oldversion" (ver modulos/sprite_rana_antigua.py).
    """
    return TIPOS_RANA[tipo].dibujar(color, boca, ojos_abiertos, escala, mirando, accesorio, postura, GEOM_BOCA)


# si no hay PNG propio, las posturas se simulan deformando el PNG de la
# postura sentada: (ancho, alto) relativos
DEFORMA_POSTURA = {1: (1.07, 0.88), 2: (0.93, 1.08), 3: (0.97, 1.05)}


MIRADAS = (-1, 0, 1)  # izquierda, al frente, derecha

# si no hay un PNG propio para un estado de boca nuevo (3,4,5,6), se usa el
# más parecido de los clásicos 0/1/2 para no obligar a redibujar los assets
ALTERNATIVA_BOCA = {3: 2, 4: 2, 5: 1, 6: 2}


def _ruta_boca(assets, nombre, boca):
    """Ruta del PNG de esa boca si existe (exacto o alternativa), o None si no hay ninguno."""
    if not assets:
        return None
    ruta = os.path.join(assets, f"rana{nombre}_boca{boca}.png")
    if os.path.exists(ruta):
        return ruta
    alt = os.path.join(assets, f"rana{nombre}_boca{ALTERNATIVA_BOCA.get(boca, 2)}.png")
    return alt if os.path.exists(alt) else None


class _SpritesRana(dict):
    """
    Sprites de una rana, generados al pedirlos por primera vez (con las
    posturas hay demasiadas combinaciones para dibujarlas todas al arrancar).
    Clave (boca, ojos_abiertos, mirada) o (boca, ojos_abiertos, mirada, postura).
    """

    def __init__(self, assets, nombre, color, escala, accesorio, tipo="nueva"):
        super().__init__()
        self.tipo = tipo
        self.assets, self.nombre, self.color = assets, nombre, color
        self.escala, self.accesorio = escala, accesorio
        self.tamano = _lienzo(escala)[:2]  # (ancho, alto) exactos, sea cual sea la resolución del PNG

    def __missing__(self, clave):
        boca, ojos, mira = clave[:3]
        postura = clave[3] if len(clave) > 3 else 0
        if self._png(boca):
            im = Image.open(self._png(boca)).convert("RGBA").resize(self.tamano, Image.LANCZOS)
            if not ojos:
                pc = os.path.join(self.assets, f"rana{self.nombre}_ojos_cerrados.png")
                if os.path.exists(pc):
                    capa = Image.open(pc).convert("RGBA").resize(self.tamano, Image.LANCZOS)
                    im = Image.alpha_composite(im, capa)
            if postura:
                fx, fy = DEFORMA_POSTURA.get(postura, (1, 1))
                im = im.resize((int(im.width * fx), int(im.height * fy)), Image.LANCZOS)
        else:
            im = rana_generada(self.color, boca, ojos, self.escala, mira, self.accesorio, postura, self.tipo)
        self[clave] = im
        return im

    def _png(self, boca):
        return _ruta_boca(self.assets, self.nombre, boca)


def cargar_sprites(assets, colores, escala, accesorios=("sombrero", "gafas"), tipo="nueva"):
    """
    Devuelve sprites[rana][(boca, ojos_abiertos, mirada[, postura])] -> RGBA.

    Por defecto dibuja las ranas por código (con su mirada, sus posturas y
    el gesto del sombrero). Si en --assets hay rana{A,B}_boca{0,1,2}.png los
    usa en su lugar para esa boca en concreto (con rana{A,B}_ojos_cerrados.png
    como capa opcional para el parpadeo); si falta alguno, esa boca en
    concreto sigue dibujándose por código, sin que haga falta aportar el
    juego completo. Los PNG propios no cambian la mirada y las posturas se
    simulan estirándolos o aplastándolos. Opcionalmente puedes añadir
    boca3.png..boca6.png (ver GEOM_BOCA); si no existen, se reutiliza el PNG
    clásico más parecido. Los sprites se generan la primera vez que se piden.
    """
    return {r: _SpritesRana(assets, nombre, colores[r], escala, accesorios[r], tipo)
            for r, nombre in enumerate("AB")}
