#!/usr/bin/env python3
"""
exportar_sprites.py — Vuelca los personajes que pasan por la escena (tractor,
cerdo, payeses, pájaros, gusano, mosquito, ovejas, perro, xeremiers...) a PNG
sueltos, listos para abrir en un editor de imagen y retocar o rehacer a mano.

Las ranas NO se exportan: se dibujan siempre por código, porque es lo que les
da la mirada (giran los ojos y el sombrero hacia donde miran) — un PNG fijo
las dejaría siempre mirando de frente.

    sprites_editables/
        eventos/
            tractor_0.png ... tractor_7.png
            cerdo_0.png ... cerdo_3.png
            payes_cuchillo_0.png ... payes_olla_3.png
            pajaro_0.png ... pajaro_7.png
            gusano_0.png ... gusano_15.png
            mosquito_0.png ... mosquito_7.png
            oveja_0.png ... oveja_11.png, perro_0.png ... perro_3.png
            xeremier_*, fabioler_*, payes_baila_*, payesa_baila_*
            payes_dret_*, payesa_ventana_*

Una vez editados, se usan así:

    python ranas.py --a A.mp3 --b B.mp3 --assets sprites_editables ...

Los fotogramas de humo del tractor no se exportan: es una simple mancha
translúcida, no un personaje, y de momento no se puede sustituir por PNG.

Ejemplo:
    python exportar_sprites.py --salida sprites_editables --escala 3
"""

import argparse
import functools
import math
import os

from modulos import eventos as ev

# (clave, función de dibujo, k = f(escala), lista de parámetros)
# Replican exactamente los k y parámetros que usa cada clase de eventos.py,
# con self.escala=1.0 (los PNG se reescalan solos a cualquier --alto al cargarlos).
def _trabajos(escala):
    SS = ev.SS
    payes_cuchillo = functools.partial(ev.dibujar_payes, arma="cuchillo")
    payes_olla = functools.partial(ev.dibujar_payes, arma="olla")
    return [
        ("tractor", ev.dibujar_tractor, SS * 0.55 * escala, [i / 8 for i in range(8)]),
        ("cerdo", ev.dibujar_cerdo_corriendo, SS * 0.75 * escala * 0.5, list(range(4))),
        ("payes_cuchillo", payes_cuchillo, SS * 0.75 * escala * 0.8, list(range(4))),
        ("payes_olla", payes_olla, SS * 0.75 * escala * 0.8, list(range(4))),
        ("pajaro", ev.dibujar_pajaro, SS * 1.0 * escala,
         [0.5 - 0.5 * math.cos(2 * math.pi * i / 8) for i in range(8)]),
        ("gusano", ev.dibujar_gusano, SS * 0.6 * escala, [i / 16 for i in range(16)]),
        ("mosquito", ev.dibujar_mosquito, SS * 0.35 * escala, list(range(8))),
        ("oveja", ev.dibujar_oveja, SS * 0.6 * escala,
         [(1 - math.cos(2 * math.pi * f / 11)) / 2 for f in range(12)]),
        ("perro", ev.dibujar_perro, SS * 0.6 * escala * 1.1, list(range(4))),
        ("xeremier", ev.dibujar_xeremier, SS * 0.65 * escala, list(range(4))),
        ("fabioler", ev.dibujar_fabioler, SS * 0.65 * escala, list(range(4))),
        ("payes_baila", ev.dibujar_payes_baila, SS * 0.65 * escala, list(range(4))),
        ("payesa_baila", ev.dibujar_payesa_baila, SS * 0.65 * escala, list(range(4))),
        ("payes_dret", ev.dibujar_payes_dret, SS * 0.22 * escala, [-2, 0, 2, 0]),
        ("payesa_ventana", ev.dibujar_payesa_ventana, SS * 0.22 * escala, [a / 3 for a in range(4)]),
    ]


def main():
    ap = argparse.ArgumentParser(description="Exporta los personajes de los eventos a PNG editables")
    ap.add_argument("--salida", default="sprites_editables", help="Carpeta destino")
    ap.add_argument("--escala", type=float, default=3.0,
                    help="Resolución de los PNG (3.0 = lienzo grande, cómodo para editar)")
    args = ap.parse_args()

    carpeta = os.path.join(args.salida, "eventos")
    os.makedirs(carpeta, exist_ok=True)
    for clave, dibujar_fn, k, params in _trabajos(args.escala):
        for i, param in enumerate(params):
            img = dibujar_fn(k, param)
            img.save(os.path.join(carpeta, f"{clave}_{i}.png"))
        print(f"  {carpeta}/{clave}_0..{len(params) - 1}.png ({img.width}x{img.height})")

    print(f"\nListo. Edita los PNG en '{carpeta}/' y luego:")
    print(f"  python ranas.py --a A.mp3 --b B.mp3 --assets {args.salida} ...")


if __name__ == "__main__":
    main()
