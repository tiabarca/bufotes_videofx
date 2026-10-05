"""
Personajes del campo con el mismo estilo que la colla y el flabioler
(modulos/sprite_colla.py, modulos/sprite_payes_tambor.py). Mismos lienzos y
parámetros que los dibujos de eventos.py / eventos_extra.py a los que sustituyen:

    cerdo_corriendo(escala, paso)       150 x 100  porc negre mallorquí al galope: orejas caídas
                                                   sobre los ojos, cerdas en el lomo, chillando
    payes_corre(escala, paso, arma)     100 x 130  la muchedumbre que lo persigue: "cuchillo" es un
                                                   pagès con barret gritando; "olla" una payesa con
                                                   rebosillo aporreando una olla con un cucharón
    oveja(escala, pasto)                 90 x 68   ovella mallorquina: lana blanca, cara blanca
    perro(escala, paso)                 100 x 76   ca de bestiar: negro, orejas de punta, lengua fuera
    payes_dret(escala, balanceo)         70 x 120  el pagès al que riñen: cabizbajo, manos a la espalda
    payesa_ventana(escala, agita)        80 x 70   la payesa en la ventana, furiosa, agitando una escoba
    motocultor(escala, fase, paso)      240 x 190  pagès con capell de palla detrás de un motocultor
                                                   viejo; el tubo de escape acaba en (182, 80)

Todos miran a la derecha y apoyan en el borde inferior del lienzo.
"""

import math

from .sprite_colla import (ARMILLA_BALL, COSSET, CORDON, DAVANTAL, FALDILLA, MANIGA, REBOSILLO, REBOSILLO_SOMBRA,
                           SABATA, _barret, _brazo, _cara, _piernas_payes, _torso_payes)
from .sprite_payes_tambor import (CALCES, CAMISA, CAMISA_SOMBRA, LINEA, MADERA, PIEL, PIEL_SOMBRA, _curva,
                                  _Lienzo)

CERDO = (36, 32, 36)
CERDO_LUZ = (64, 58, 64)
CERDO_MORRO = (82, 66, 72)
OVEJA = (246, 244, 236)
OVEJA_SOMBRA = (214, 210, 198)
OVEJA_CARA = (236, 228, 214)
PERRO = (30, 28, 30)
PERRO_LUZ = (62, 58, 62)
LENGUA = (222, 106, 120)
ACERO = (214, 218, 224)
OLLA = (112, 116, 126)
OLLA_LUZ = (160, 164, 174)
PALLA = (222, 196, 120)
PALLA_OSC = (180, 150, 80)
MOTOR = (206, 72, 40)
MOTOR_OSC = (150, 46, 26)
METAL = (70, 70, 76)
METAL_LUZ = (120, 120, 128)
TIERRA = (120, 90, 62)
PANTALON = (70, 64, 58)


def _patas(lz, xs_y, suelo, osc, signos, color, ancho=(6, 4), pezuna=None):
    """Patas finas al trote/galope: cada una de (x, y_cadera) a la pezuña, que se adelanta o atrasa."""
    for (x, y), sig in zip(xs_y, signos):
        px = x + osc * sig
        rod = ((x + px) / 2 + 2 * sig * (1 if osc else 0), (y + suelo) / 2)
        lz.tubo([(x, y), rod, (px, suelo - 2)], [ancho[0], (ancho[0] + ancho[1]) / 2, ancho[1]], color)
        if pezuna:
            lz.elipse(px + 0.6, suelo - 1.6, ancho[1] * 0.75, 1.8, pezuna, ancho=0.8)


# ----------------------------------------------------------------------------
# Persecución del cerdo
# ----------------------------------------------------------------------------

def cerdo_corriendo(escala, paso=0, suavizado=4):
    lz = _Lienzo(escala, suavizado, 150, 100)
    p = paso % 4
    osc = (0, 13, 0, -13)[p]   # al galope: manos adelante y patas atrás, y luego recogidas
    bote = (0, -4, 0, -1)[p]
    flap = (0, -4, -2, 3)[p]
    cy = 50 + bote
    # patas del lado de allá (más oscuras)
    _patas(lz, [(46, cy + 14), (104, cy + 14)], 98, osc, (-1, 1), (22, 20, 22), (9, 6), (12, 10, 12))
    lz.tubo(_curva((26, cy - 10), (12, cy - 16), (16, cy - 2), 8), [4, 3.6, 3.2, 3, 2.8, 2.6, 2.4, 2.2, 2],
            CERDO)  # cola rizada, tiesa del susto
    lz.elipse(74, cy, 54, 24, CERDO, ancho=1.6)  # cuerpo
    lz.poli(_curva((30, cy - 10), (70, cy - 30), (116, cy - 14), 10) +
            _curva((110, cy - 6), (70, cy - 18), (36, cy - 2), 10), CERDO_LUZ, outline=None)  # brillo del lomo
    for i in range(11):  # cerdas del lomo
        x = 32 + i * 8
        y = cy - 23 + 0.0045 * (x - 74) ** 2
        lz.linea([(x, y), (x - 2.5, y - 5)], CERDO, 1.4)
    # cabeza redondeada con hocico largo, un poco agachada al correr
    lz.elipse(122, cy - 6, 16, 15, CERDO, ancho=1.6)
    lz.poli([(126, cy - 16), (144, cy - 6), (146, cy + 4), (128, cy + 8)], CERDO)
    lz.elipse(145, cy - 1, 3.6, 6, CERDO_MORRO, ancho=1.2)
    lz.elipse(145.5, cy - 3, 0.9, 1.4, LINEA, outline=None)
    lz.elipse(145.5, cy + 1.5, 0.9, 1.4, LINEA, outline=None)
    lz.elipse(137, cy + 7, 4, 2.4, (130, 40, 50), ancho=1.0)  # boca abierta: chilla
    lz.elipse(129, cy - 8, 3.4, 3.6, (255, 255, 255), ancho=0.9)  # ojo de susto
    lz.elipse(130, cy - 8, 1.4, 1.5, LINEA, outline=None)
    # oreja grande caída hacia delante, sobre el ojo (como la del porc negre de verdad), ondeando
    lz.poli([(112, cy - 18), (122, cy - 22), (138, cy - 14 + flap), (132, cy - 8 + flap * 0.6), (118, cy - 10)],
            CERDO_LUZ)
    # patas del lado de acá
    _patas(lz, [(54, cy + 16), (112, cy + 16)], 98, osc, (-1, 1), CERDO, (9, 6), (12, 10, 12))
    if p in (1, 3):  # líneas de velocidad
        for y in (cy - 12, cy, cy + 12):
            lz.linea([(2, y), (14, y)], (240, 240, 240), 1.2)
    return lz.reducir()


def payes_corre(escala, paso=0, arma="cuchillo", suavizado=4):
    lz = _Lienzo(escala, suavizado, 100, 130)
    p = paso % 4
    osc = (0, 12, 0, -12)[p]
    sube = 8 if p % 2 == 0 else 0
    cx, suelo, cintura = 42, 128, 86
    lean = 4  # inclinados hacia delante al correr
    if arma == "olla":
        # payesa: faldilla recogida al correr, rebosillo, olla y cucharón
        for x, sig in ((cx - 6, 1), (cx + 6, -1)):
            pie = x + osc * sig
            lz.poli([(x - 3, cintura + 22), (x + 3, cintura + 22), (pie + 3, suelo - 5), (pie - 3, suelo - 5)], CALCES)
            lz.elipse(pie + 1.5, suelo - 3, 5.5, 3, SABATA)
        lz.poli([(cx - 12, cintura - 4), (cx + 12, cintura - 4), (cx + 22 + osc * 0.3, cintura + 26),
                 (cx, cintura + 22), (cx - 22 - osc * 0.3, cintura + 26)], FALDILLA)
        lz.poli([(cx - 8, cintura - 2), (cx + 8, cintura - 2), (cx + 12, cintura + 20), (cx - 12, cintura + 20)],
                DAVANTAL)
        lz.poli([(cx - 14 + lean, 54), (cx + 14 + lean, 54), (cx + 12, cintura), (cx - 12, cintura)], COSSET)
        for i in range(3):
            y = 60 + i * 5
            lz.linea([(cx + lean - 3, y), (cx + lean + 4, y + 3)], CORDON, 0.9)
            lz.linea([(cx + lean + 4, y), (cx + lean - 3, y + 3)], CORDON, 0.9)
        brazo_atras = ((cx - 12 + lean, 58), (cx - 24, 66), (cx - 20 - osc * 0.4, 76))
        _brazo(lz, *brazo_atras, manga=MANIGA)
        hy = 36
        lz.poli(_curva((cx - 17 + lean, hy + 4), (cx + lean, hy - 28), (cx + 17 + lean, hy + 4), 12) +
                [(cx + 19 + lean, 56), (cx + 6 + lean, 64), (cx + lean, 68), (cx - 6 + lean, 64), (cx - 19 + lean, 56)],
                REBOSILLO)
        lz.linea(_curva((cx - 14 + lean, 56), (cx + lean, 62), (cx + 14 + lean, 56), 8), REBOSILLO_SOMBRA, 1.0)
        _cara(lz, cx + lean, hy, bigote=False, boca="grito", mujer=True, cejas="enfado")
        # olla en alto y cucharón
        mano = (cx + 36, 26 - sube)
        _brazo(lz, (cx + 12 + lean, 58), (cx + 28, 46), mano, manga=MANIGA)
        lz.poli([(mano[0] - 8, mano[1] - 14), (mano[0] + 12, mano[1] - 14), (mano[0] + 10, mano[1] - 2),
                 (mano[0] - 6, mano[1] - 2)], OLLA)
        lz.elipse(mano[0] + 2, mano[1] - 14, 10, 2.6, OLLA_LUZ, ancho=1.1)
        lz.linea([(mano[0] - 8, mano[1] - 10), (mano[0] - 12, mano[1] - 10)], OLLA, 2.0)  # asa
        cuchara = (cx + 26, 12 + sube * 0.5)
        lz.linea([(mano[0] + 2, mano[1] - 15), cuchara], MADERA, 2.0)
        lz.elipse(cuchara[0], cuchara[1], 3, 2.2, MADERA, ancho=0.8)
        if p % 2 == 0:  # ¡clang!
            for a in (-40, -80, -120):
                ra = math.radians(a)
                lz.linea([(mano[0] + 2 + math.cos(ra) * 14, mano[1] - 16 + math.sin(ra) * 6),
                          (mano[0] + 2 + math.cos(ra) * 20, mano[1] - 16 + math.sin(ra) * 10)], (255, 240, 170), 1.4)
        return lz.reducir()

    # pagès con barret, gritando, cuchillo en alto
    _piernas_payes(lz, (cx - 8, cx + 8), cintura, suelo, (osc, -osc))
    brazo_atras = ((cx - 16 + lean, 56), (cx - 26, 66), (cx - 22 - osc * 0.4, 78))
    _brazo(lz, *brazo_atras)
    _torso_payes(lz, cx + lean / 2, 52, cintura, ARMILLA_BALL, (170, 40, 40), ancho=19)
    hy = 33
    _cara(lz, cx + lean, hy, bigote=True, boca="grito", cejas="enfado")
    _barret(lz, cx + lean, hy - 11, inclina=-8)
    mano = (cx + 34, 24 - sube)
    _brazo(lz, (cx + 16 + lean, 56), (cx + 28, 44), mano)
    lz.poli([(mano[0] + 1, mano[1] - 3), (mano[0] + 16, mano[1] - 20), (mano[0] + 6, mano[1] + 1)], ACERO,
            ancho=1.0)  # hoja
    lz.linea([(mano[0] + 3, mano[1] - 5), (mano[0] + 13, mano[1] - 17)], (250, 250, 255), 0.8)  # brillo
    return lz.reducir()


# ----------------------------------------------------------------------------
# Ovejas y perro
# ----------------------------------------------------------------------------

def oveja(escala, pasto=0.0, suavizado=4):
    lz = _Lienzo(escala, suavizado, 90, 68)
    dy = 14 * pasto
    _patas(lz, [(30, 46), (64, 46)], 68, 0, (1, 1), OVEJA_SOMBRA, (5, 4), (60, 54, 50))  # de detrás
    # lana a bultos
    for cx, cy, r in ((26, 36, 14), (40, 28, 14), (56, 28, 14), (66, 38, 12), (44, 42, 16), (30, 46, 10),
                      (58, 46, 10)):
        lz.elipse(cx, cy, r, r * 0.86, OVEJA, outline=OVEJA_SOMBRA, ancho=1.2)
    for cx, cy in ((36, 24), (52, 24), (44, 34)):  # rizos
        lz.linea(_curva((cx - 3, cy), (cx, cy - 3), (cx + 3, cy), 4), OVEJA_SOMBRA, 1.0)
    lz.elipse(13, 36, 4, 5, OVEJA, outline=OVEJA_SOMBRA)  # cola
    # cabeza blanca, alargada
    hx, hy = 76, 28 + dy
    lz.poli([(hx - 8, hy - 6), (hx + 4, hy - 8), (hx + 12, hy + 2), (hx + 10, hy + 9), (hx - 4, hy + 8)],
            OVEJA_CARA, outline=(170, 160, 146), ancho=1.1)
    lz.elipse(hx - 6, hy - 5, 6, 2.4, OVEJA_CARA, outline=(170, 160, 146), ancho=1.0)  # oreja de lado
    lz.elipse(hx + 2, hy - 2, 1.4, 1.2, LINEA, outline=None)  # ojo
    lz.elipse(hx + 10, hy + 5, 1.8, 1.4, (120, 100, 96), outline=None)  # morro
    lz.elipse(hx - 4, hy - 9, 6, 4, OVEJA, outline=OVEJA_SOMBRA, ancho=1.0)  # tupé de lana
    _patas(lz, [(24, 48), (58, 48)], 68, 0, (1, 1), OVEJA_CARA, (5.5, 4.2), (60, 54, 50))
    if pasto > 0.6:  # hierba en la boca
        lz.linea([(hx + 9, hy + 8), (hx + 13, hy + 12)], (90, 150, 60), 1.2)
    return lz.reducir()


def perro(escala, paso=0, suavizado=4):
    lz = _Lienzo(escala, suavizado, 100, 76)
    p = paso % 4
    osc = (0, 10, 0, -10)[p]
    bote = (0, -3, 0, -1)[p]
    _patas(lz, [(26, 44 + bote), (66, 44 + bote)], 76, osc, (-1, 1), (18, 18, 20), (6, 4), (10, 10, 10))
    lz.tubo(_curva((20, 32 + bote), (8, 26 + bote), (6, 14 + bote), 8), [6, 5.5, 5, 4.5, 4, 3.5, 3, 2.5, 2], PERRO)
    lz.elipse(46, 36 + bote, 30, 13, PERRO, ancho=1.4)
    lz.poli(_curva((22, 30 + bote), (46, 22 + bote), (70, 28 + bote), 8) + [(64, 33 + bote), (28, 34 + bote)],
            PERRO_LUZ, outline=None)
    # cuello y cabeza
    lz.poli([(64, 30 + bote), (76, 16 + bote), (86, 20 + bote), (78, 40 + bote)], PERRO)
    lz.poli([(74, 18 + bote), (82, 10 + bote), (92, 16 + bote), (99, 24 + bote), (96, 30 + bote), (84, 32 + bote),
             (74, 28 + bote)], PERRO)
    lz.poli([(76, 16 + bote), (77, 2 + bote), (84, 12 + bote)], PERRO)  # oreja de punta
    lz.elipse(98, 24 + bote, 2, 1.8, (10, 10, 10), outline=None)  # trufa
    lz.elipse(86, 19 + bote, 2.0, 1.7, (230, 190, 70), ancho=0.6)  # ojo ámbar
    lz.elipse(86.4, 19 + bote, 0.8, 0.8, LINEA, outline=None)
    lz.tubo([(90, 30 + bote), (92, 36 + bote), (89, 40 + bote)], [3.4, 3.2, 2.6], LENGUA, outline=(150, 60, 70))
    _patas(lz, [(32, 46 + bote), (72, 46 + bote)], 76, osc, (-1, 1), PERRO, (6, 4), (10, 10, 10))
    return lz.reducir()


# ----------------------------------------------------------------------------
# Los de la possessió
# ----------------------------------------------------------------------------

def payes_dret(escala, balanceo=0, suavizado=4):
    """Cabizbajo y con las manos a la espalda mientras le riñen. balanceo: unos píxeles de vaivén."""
    lz = _Lienzo(escala, suavizado, 70, 120)
    b = balanceo * 0.6
    cx, suelo, cintura = 35, 119, 80
    _piernas_payes(lz, (cx - 7, cx + 7), cintura, suelo, (b * 0.3, -b * 0.3))
    _brazo(lz, (cx - 16 + b, 46), (cx - 20 + b, 62), (cx - 10 + b, 72), piel=False)  # manos a la espalda
    _brazo(lz, (cx + 16 + b, 46), (cx + 20 + b, 62), (cx + 10 + b, 72), piel=False)
    _torso_payes(lz, cx + b, 42, cintura, ARMILLA_BALL, (40, 70, 140), ancho=17)
    hy = 27
    _cara(lz, cx + b * 1.2, hy, ojos="cerrados", bigote=True, boca="morros")
    lz.linea([(cx - 7 + b, hy - 6), (cx - 1 + b, hy - 4.5)], LINEA, 1.2)  # cejas de "ya voy..."
    lz.linea([(cx + 3 + b, hy - 4.5), (cx + 9 + b, hy - 6)], LINEA, 1.2)
    _barret(lz, cx + b * 1.2, hy - 11, inclina=6)
    lz.elipse(cx + 16 + b, hy - 8, 1.4, 2.2, (150, 200, 240), ancho=0.6)  # gota de sudor
    return lz.reducir()


def payesa_ventana(escala, agita=0.0, suavizado=4):
    """Asomada a la ventana, furiosa, agitando la escoba. agita 0..1 mueve la escoba de lado a lado."""
    lz = _Lienzo(escala, suavizado, 80, 70)
    cx = 32
    lz.poli([(cx - 18, 44), (cx + 18, 44), (cx + 20, 70), (cx - 20, 70)], COSSET)
    for i in range(3):
        y = 50 + i * 5
        lz.linea([(cx - 4, y), (cx + 4, y + 3)], CORDON, 0.9)
        lz.linea([(cx + 4, y), (cx - 4, y + 3)], CORDON, 0.9)
    _brazo(lz, (cx - 16, 48), (cx - 22, 60), (cx - 12, 64), manga=MANIGA)  # en jarras
    hy = 26
    lz.poli(_curva((cx - 17, hy + 4), (cx, hy - 28), (cx + 17, hy + 4), 12) +
            [(cx + 19, 46), (cx + 6, 54), (cx, 58), (cx - 6, 54), (cx - 19, 46)], REBOSILLO)
    lz.linea(_curva((cx - 14, 46), (cx, 52), (cx + 14, 46), 8), REBOSILLO_SOMBRA, 1.0)
    _cara(lz, cx, hy, bigote=False, boca="grito", mujer=True, cejas="enfado")
    # escoba agitándose
    ang = math.radians(-100 + agita * 50)  # de casi vertical a inclinada: no se sale del lienzo
    mano = (cx + 24, 34)
    _brazo(lz, (cx + 16, 48), (cx + 24, 44), mano, manga=MANIGA)
    punta = (mano[0] + math.cos(ang) * 20, mano[1] + math.sin(ang) * 20)
    cola = (mano[0] - math.cos(ang) * 10, mano[1] - math.sin(ang) * 10)
    lz.linea([cola, punta], MADERA, 2.4)
    nx, ny = -math.sin(ang), math.cos(ang)
    dxp, dyp = math.cos(ang), math.sin(ang)
    lz.poli([(punta[0] + nx * 3, punta[1] + ny * 3), (punta[0] - nx * 3, punta[1] - ny * 3),
             (punta[0] + dxp * 12 - nx * 7, punta[1] + dyp * 12 - ny * 7),
             (punta[0] + dxp * 12 + nx * 7, punta[1] + dyp * 12 + ny * 7)], PALLA, ancho=1.0)
    for j in (-4, 0, 4):
        lz.linea([(punta[0] + dxp * 3 + nx * j * 0.5, punta[1] + dyp * 3 + ny * j * 0.5),
                  (punta[0] + dxp * 12 + nx * j, punta[1] + dyp * 12 + ny * j)], PALLA_OSC, 0.7)
    lz.elipse(mano[0], mano[1], 3.6, 3.2, PIEL)
    return lz.reducir()


# ----------------------------------------------------------------------------
# Motocultor
# ----------------------------------------------------------------------------

def motocultor(escala, fase=0.0, paso=0, suavizado=4):
    lz = _Lienzo(escala, suavizado, 240, 190)
    zanc = 12 * math.sin(paso * math.pi / 2)
    # --- pagès caminando detrás (a la izquierda), con capell de palla
    cx, suelo = 48, 188
    for x, sig, col in ((cx - 6, -1, (54, 50, 46)), (cx + 6, 1, PANTALON)):
        pie = x + zanc * sig
        lz.tubo([(x, 128), ((x + pie) / 2, 158), (pie, suelo - 6)], [11, 10, 9], col)
        lz.elipse(pie + 3, suelo - 4, 8, 4, (40, 32, 26))
    lz.poli([(cx - 16, 82), (cx + 16, 82), (cx + 18, 130), (cx - 18, 130)], CAMISA)
    lz.linea([(cx - 12, 90), (cx - 13, 124)], CAMISA_SOMBRA, 2.0)
    lz.poli([(cx - 18, 124), (cx + 18, 124), (cx + 18, 132), (cx - 18, 132)], (60, 50, 40))  # cinturón
    lz.elipse(cx + 2, 128, 3, 3, (200, 170, 80), ancho=0.8)
    # cabeza
    hy = 64
    lz.elipse(cx + 2, hy, 14, 15, PIEL)
    lz.elipse(cx - 11, hy + 1, 3, 4, PIEL_SOMBRA, ancho=1.0)
    lz.elipse(cx + 8, hy - 1, 1.6, 2.0, LINEA, outline=None)
    lz.elipse(cx + 14, hy + 4, 3.2, 4.2, PIEL_SOMBRA, ancho=1.0)
    lz.elipse(cx + 8, hy + 8, 3.6, 2.4, (226, 140, 120), outline=None)
    lz.linea(_curva((cx + 4, hy + 11), (cx + 9, hy + 13), (cx + 13, hy + 10), 5), LINEA, 1.2)
    lz.linea([(cx + 4, hy + 13), (cx + 3, hy + 18), (cx + 6, hy + 18)], (90, 90, 90), 0.8)  # barba de tres días
    # capell de palla
    lz.poli([(cx - 22, hy - 8), (cx + 26, hy - 8), (cx + 24, hy - 4), (cx - 20, hy - 4)], PALLA, ancho=1.2)
    lz.poli([(cx - 10, hy - 6), (cx - 8, hy - 20), (cx + 12, hy - 20), (cx + 14, hy - 6)], PALLA, ancho=1.2)
    lz.poli([(cx - 10, hy - 10), (cx + 14, hy - 10), (cx + 14, hy - 7), (cx - 10, hy - 7)], (150, 40, 40),
            outline=None)
    for j in range(5):
        lz.linea([(cx - 6 + j * 4, hy - 19), (cx - 7 + j * 4.5, hy - 7)], PALLA_OSC, 0.6)
    # brazos al manillar
    _brazo(lz, (cx + 12, 88), (cx + 26, 104), (94, 102))
    # --- manillares
    lz.tubo([(90, 98), (120, 118), (150, 136)], [5, 5, 6], METAL)
    lz.tubo([(94, 106), (122, 124), (150, 142)], [4, 4, 5], METAL_LUZ)
    lz.elipse(91, 99, 4, 3, (30, 30, 30))
    # --- motor
    lz.poli([(136, 110), (204, 110), (206, 150), (134, 150)], MOTOR, ancho=1.6)
    lz.poli([(140, 114), (200, 114), (200, 120), (140, 120)], (236, 110, 70), outline=None)  # brillo
    for j in range(5):  # aletas de refrigeración
        y = 124 + j * 5
        lz.linea([(142, y), (168, y)], MOTOR_OSC, 1.4)
    lz.poli([(146, 92), (176, 92), (178, 110), (144, 110)], (40, 90, 60), ancho=1.3)  # depósito
    lz.elipse(160, 92, 5, 2, METAL_LUZ, ancho=0.9)  # tapón
    lz.elipse(194, 100, 7, 7, METAL, ancho=1.2)  # filtro de aire
    lz.tubo([(182, 110), (182, 94), (182, 82)], [7, 7, 7], METAL)  # tubo de escape
    lz.poli([(177, 82), (187, 82), (186, 78), (178, 78)], (40, 40, 44))
    lz.linea([(180, 108), (180, 86)], METAL_LUZ, 1.2)
    # rueda con tacos
    wx, wy, r = 162, 162, 22
    lz.elipse(wx, wy, r, r, (34, 32, 32), ancho=1.6)
    for i in range(14):
        a = 2 * math.pi * (i / 14 + fase / 14)
        lz.linea([(wx + math.cos(a) * (r - 4), wy + math.sin(a) * (r - 4)),
                  (wx + math.cos(a) * (r + 1), wy + math.sin(a) * (r + 1))], (70, 66, 64), 3.0)
    lz.elipse(wx, wy, 10, 10, (190, 190, 196), ancho=1.2)
    lz.elipse(wx, wy, 3, 3, METAL, ancho=0.8)
    # fresa: cuchillas curvas que giran y levantan tierra
    fx, fy, fr = 214, 166, 21
    for i in range(8):
        a = 2 * math.pi * (i / 8 + fase / 8)
        b = a + 0.5
        lz.tubo([(fx + math.cos(a) * 5, fy + math.sin(a) * 5), (fx + math.cos(a) * fr * 0.7, fy + math.sin(a) * fr * 0.7),
                 (fx + math.cos(b) * fr * 0.9, fy + math.sin(b) * fr * 0.9)], [3.4, 3.0, 2.4], (150, 150, 158))
    lz.elipse(fx, fy, 5, 5, METAL, ancho=0.9)
    guarda = [(fx + math.cos(math.radians(a)) * (fr + 4), fy + math.sin(math.radians(a)) * (fr + 4))
              for a in range(180, 361, 15)]
    guarda += [(fx + math.cos(math.radians(a)) * (fr + 1), fy + math.sin(math.radians(a)) * (fr + 1))
               for a in range(360, 179, -15)]
    lz.poli(guarda, MOTOR, ancho=1.2)  # guardabarros por encima de la fresa
    lz.tubo([(200, 140), (fx - 6, fy - fr - 2)], [5, 5], METAL)  # brazo que une la fresa al motor
    for i in range(4):  # terrones que salen despedidos
        a = math.radians(-30 - i * 25 + fase * 40)
        d = 26 + (i * 7 + fase * 20) % 14
        lz.elipse(fx + math.cos(a) * d + 6, fy - 10 + math.sin(a) * d * 0.6, 2.4, 2.0, TIERRA, ancho=0.6)
    return lz.reducir()
