#!/usr/bin/env python3
"""
crear_sprites_cabra.py — Vuelca los sprites de la cabra mallorquina a PNG en
sprites_editables/eventos/, para retocarlos a mano y usarlos con --assets.

    cabra_0.png ... cabra_5.png   la coz por pasos: 0 = de pie, 5 = coz en todo lo alto
    cabra_coz_0.png               el instante del impacto (con estallido en las pezuñas)

Sin --assets, el vídeo ya usa este mismo dibujo (modulos/sprite_cabra.py).
Con --assets sprites_editables, si existen estos PNG se usan en su lugar.

    python crear_sprites_cabra.py
    python crear_sprites_cabra.py --salida otra_carpeta --escala 4
"""

import argparse
import os

from modulos.sprite_cabra import PASOS_COZ, dibujar


def main():
    ap = argparse.ArgumentParser(description="Sprites PNG de la cabra mallorquina")
    ap.add_argument("--salida", default="sprites_editables", help="Carpeta base (se usa <salida>/eventos/)")
    ap.add_argument("--escala", type=float, default=3.0, help="Resolución (3.0 = 330x480 px)")
    args = ap.parse_args()
    carpeta = os.path.join(args.salida, "eventos")
    os.makedirs(carpeta, exist_ok=True)
    for i, fase in enumerate(PASOS_COZ):
        dibujar(args.escala, fase).save(os.path.join(carpeta, f"cabra_{i}.png"))
    dibujar(args.escala, 1.0, impacto=True).save(os.path.join(carpeta, "cabra_coz_0.png"))
    print(f"  {carpeta}/cabra_0..{len(PASOS_COZ) - 1}.png y cabra_coz_0.png")
    print(f"\nListo. Edítalos si quieres y luego: python ranas.py ... --assets {args.salida}")


if __name__ == "__main__":
    main()
