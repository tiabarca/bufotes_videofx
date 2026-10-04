"""
Pista MIDI -> eventos de la escena.

Cada nota del MIDI lanza un evento en el instante en que suena. Así se pueden
sincronizar a mano los gags con el audio: en el DAW se añade una pista MIDI
encima del podcast, se ponen notas donde quieres que pase algo y se exporta
como .mid.

Sin dependencias: incluye un lector de Standard MIDI File (tipos 0 y 1) que
respeta los cambios de tempo.

Mapa evento -> notas
--------------------
Se configura en midi_mapa.ini (junto a ranas.py), una línea por evento con
las notas que lo lanzan, separadas por comas:

    cerdo_asoma = Do, C2, 61
    grillo      = Re, Re#
    pedo        = nada        # este evento no se lanza desde MIDI

Valen nombres latinos (Do, Re#, Sib) o ingleses (C, D#, Bb), con o sin octava
(C3 = nota 60, como Ableton/Cubase), y números 0-127. Una nota sin octava vale
para todas las octavas; si una tecla encaja en varias, gana la más concreta:
número > nota con octava > nota sin octava. Las notas que no aparecen no hacen nada.

Si no existe el archivo se usa este mapa por defecto:

    C  (Do)   cerdo_asoma   el cerdo sale por abajo; se queda mientras dure la nota
    D  (Re)   grillo        un grillo cruza a saltos por delante
    E  (Mi)   pajaros
    F  (Fa)   gusano
    G  (Sol)  tractor
    A  (La)   cerdo         el cerdo que pasea y husmea
"""

import json
import os
import re
import struct

NOMBRES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

MAPA_POR_DEFECTO = {
    "C": "cerdo_asoma",
    "D": "grillo",
    "E": "pajaros",
    "F": "gusano",
    "G": "tractor",
    "A": "cerdo",
}


class Nota:
    __slots__ = ("nota", "canal", "inicio", "fin", "velocidad", "pista")

    def __init__(self, nota, canal, inicio, fin, velocidad, pista):
        self.nota, self.canal, self.inicio, self.fin = nota, canal, inicio, fin
        self.velocidad, self.pista = velocidad, pista

    @property
    def nombre(self):
        return f"{NOMBRES[self.nota % 12]}{self.nota // 12 - 2}"  # C3 = 60

    def __repr__(self):
        return f"<{self.nombre} {self.inicio:.2f}s-{self.fin:.2f}s v{self.velocidad}>"


# ----------------------------------------------------------------------------
# Lector de Standard MIDI File
# ----------------------------------------------------------------------------

def _vlq(datos, pos):
    valor = 0
    while True:
        b = datos[pos]
        pos += 1
        valor = (valor << 7) | (b & 0x7F)
        if not b & 0x80:
            return valor, pos


def _leer_pista(datos, n_pista):
    """Devuelve [(tick, tipo, datos...)] con ticks absolutos."""
    eventos = []
    pos, tick, estado = 0, 0, None
    while pos < len(datos):
        delta, pos = _vlq(datos, pos)
        tick += delta
        b = datos[pos]
        if b == 0xFF:  # meta
            tipo = datos[pos + 1]
            largo, pos = _vlq(datos, pos + 2)
            if tipo == 0x51 and largo == 3:  # tempo
                eventos.append((tick, "tempo", int.from_bytes(datos[pos:pos + 3], "big")))
            elif tipo == 0x2F:  # fin de pista
                break
            pos += largo
            continue
        if b in (0xF0, 0xF7):  # sysex
            largo, pos = _vlq(datos, pos + 1)
            pos += largo
            continue
        if b & 0x80:
            estado = b
            pos += 1
        elif estado is None:
            raise ValueError(f"MIDI corrupto en la pista {n_pista}")
        tipo, canal = estado & 0xF0, estado & 0x0F
        n_datos = 1 if tipo in (0xC0, 0xD0) else 2
        d = datos[pos:pos + n_datos]
        pos += n_datos
        if tipo == 0x90 and d[1] > 0:
            eventos.append((tick, "on", canal, d[0], d[1], n_pista))
        elif tipo == 0x80 or (tipo == 0x90 and d[1] == 0):
            eventos.append((tick, "off", canal, d[0], 0, n_pista))
    return eventos


def leer_notas(ruta, tempo_fijo=None):
    """
    Lee un .mid y devuelve las notas con tiempos en segundos, ordenadas.

    tempo_fijo: BPM a usar para todo el archivo, ignorando los eventos de
    tempo que traiga (o el valor por defecto de 120 si no trae ninguno).
    Muchos DAW, al exportar una pista MIDI que solo son marcadores de
    tiempo (no música de verdad), no incrustan el tempo real del proyecto
    (o incrustan 120 a secas); si los eventos salen descuadrados respecto
    al audio, es casi seguro que sea esto, y el BPM real del proyecto es
    tempo_defecto * (tiempo_que_sale / tiempo_que_debería_salir).
    """
    with open(ruta, "rb") as f:
        datos = f.read()
    if datos[:4] != b"MThd":
        raise ValueError(f"{ruta} no parece un archivo MIDI")
    largo_cab = struct.unpack(">I", datos[4:8])[0]
    _formato, n_pistas, division = struct.unpack(">HHH", datos[8:14])
    if division & 0x8000:
        raise ValueError("MIDI con división SMPTE no soportado: expórtalo con ticks por negra")
    ppq = division
    pos = 8 + largo_cab

    eventos = []
    for n in range(n_pistas):
        if datos[pos:pos + 4] != b"MTrk":
            break
        largo = struct.unpack(">I", datos[pos + 4:pos + 8])[0]
        eventos += _leer_pista(datos[pos + 8:pos + 8 + largo], n)
        pos += 8 + largo

    # ticks -> segundos con el mapa de tempo (los tempos van antes que las notas del mismo tick)
    eventos.sort(key=lambda e: (e[0], 0 if e[1] == "tempo" else 1))
    tempo_inicial = round(60e6 / tempo_fijo) if tempo_fijo else 500000  # 120 bpm por defecto
    tempo, tick_ant, seg = tempo_inicial, 0, 0.0
    abiertas, notas = {}, []
    for e in eventos:
        seg += (e[0] - tick_ant) * tempo / ppq / 1e6
        tick_ant = e[0]
        if e[1] == "tempo":
            if not tempo_fijo:  # con tempo_fijo se ignoran los cambios de tempo del archivo
                tempo = e[2]
            continue
        _, tipo, canal, nota, vel, pista = e
        clave = (canal, nota)
        if tipo == "on":
            abiertas.setdefault(clave, []).append((seg, vel, pista))
        elif abiertas.get(clave):
            ini, v, p = abiertas[clave].pop(0)
            notas.append(Nota(nota, canal, ini, seg, v, p))
    for (canal, nota), lista in abiertas.items():  # notas sin note-off
        for ini, v, p in lista:
            notas.append(Nota(nota, canal, ini, ini + 0.5, v, p))
    notas.sort(key=lambda x: x.inicio)
    return notas


# ----------------------------------------------------------------------------
# Notas -> eventos
# ----------------------------------------------------------------------------

LATINAS = {"DO": "C", "RE": "D", "MI": "E", "FA": "F", "SOL": "G", "LA": "A", "SI": "B"}
_RE_NOTA = re.compile(r"^(DO|RE|MI|FA|SOL|LA|SI|[A-G])([#B]?)(-?\d+)?$")

MAPA_ARCHIVO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "midi_mapa.ini")  # raíz del proyecto, no modulos/
NADA = {"", "-", "NADA", "NINGUNO", "NONE", "NULL", "OFF"}


def _normalizar(clave):
    """'60' -> '60', 'Do#3' / 'C#3' / 'Db3' -> 'C#3', 're' / 'D' -> 'D'. None si no es una nota."""
    c = str(clave).strip().upper().replace("♯", "#").replace("♭", "B").replace(" ", "")
    if c.isdigit():
        return c if 0 <= int(c) <= 127 else None
    m = _RE_NOTA.match(c)
    if not m:
        return None
    base, alt, octava = m.group(1), m.group(2), m.group(3) or ""
    idx = NOMBRES.index(LATINAS.get(base, base))
    idx = (idx + (1 if alt == "#" else -1 if alt == "B" else 0)) % 12
    return NOMBRES[idx] + octava


def _leer_ini(ruta):
    """Formato 'evento = nota, nota, ...', una línea por evento. # o ; para comentarios."""
    pares = []
    with open(ruta, encoding="utf-8-sig") as f:
        for n, linea in enumerate(f, 1):
            linea = re.sub(r"\s[#;].*$", "", linea).strip()  # comentario al final de la línea
            if not linea or linea[0] in "#;[":
                continue
            if "=" not in linea:
                print(f"  Aviso: {os.path.basename(ruta)} línea {n}: falta '=' ({linea})")
                continue
            evento, notas = (x.strip() for x in linea.split("=", 1))
            pares.append((n, evento, [x for x in re.split(r"[,\s]+", notas) if x]))
    return pares


def cargar_mapa(ruta=None):
    """
    Mapa nota -> evento, construido a partir de un archivo 'evento = notas':

        cerdo_asoma = Do, C2, 61
        grillo      = Re

    Se lee el archivo pasado con --midi-mapa o, si no, midi_mapa.ini junto a
    este script. Si hay archivo, define el mapa entero (las notas que no salen
    no hacen nada). Sin archivo se usa MAPA_POR_DEFECTO. También admite .json
    con la misma forma: {"cerdo_asoma": ["Do", "C2"], ...}.
    """
    if ruta is None and os.path.exists(MAPA_ARCHIVO):
        ruta = MAPA_ARCHIVO
    if not ruta:
        return {_normalizar(k): v for k, v in MAPA_POR_DEFECTO.items()}
    if ruta.lower().endswith(".json"):
        with open(ruta, encoding="utf-8") as f:
            pares = [(0, ev, [notas] if isinstance(notas, (str, int)) else list(notas or []))
                     for ev, notas in json.load(f).items()]
    else:
        pares = _leer_ini(ruta)
    nombre = os.path.basename(ruta)
    mapa = {}
    for n, evento, notas in pares:
        evento = evento.strip().lower()
        if len(notas) == 1 and str(notas[0]).strip().upper() in NADA:
            continue  # evento sin notas: no se lanza desde MIDI
        for nota in notas:
            clave = _normalizar(nota)
            if clave is None:
                print(f"  Aviso: {nombre} línea {n}: '{nota}' no es una nota válida")
                continue
            if clave in mapa and mapa[clave] != evento:
                print(f"  Aviso: {nombre} línea {n}: la nota {nota} ya lanzaba '{mapa[clave]}', "
                      f"ahora lanza '{evento}'")
            mapa[clave] = evento
    print(f"  Mapa MIDI: {nombre}")
    return mapa


def evento_de_nota(nota, mapa):
    """Busca la nota por número, luego por nombre con octava y luego por nombre."""
    for clave in (str(nota.nota), nota.nombre, NOMBRES[nota.nota % 12]):
        if clave in mapa:
            return mapa[clave]
    return None


def eventos_midi(ruta, fps, W, H, tipos, mapa=None, desfase=0.0, canal=None,
                 n_frames=None, semilla=0, max_simultaneos=6, tempo=None):
    """
    Devuelve [(fotograma_inicio, evento)] listo para mezclar con la agenda aleatoria,
    y un resumen {nombre_nota: tipo} de lo que se ha usado.

    - tipos: diccionario nombre -> clase de evento (eventos.TIPOS)
    - desfase: segundos a sumar a todas las notas (si el MIDI empieza antes o después)
    - canal: 1-16 para usar solo ese canal; None, todos
    - tempo: BPM fijo a forzar si los eventos salen descuadrados del audio (ver leer_notas)
    - Cada evento recibe .velocidad (1-127) y .mantener (fotogramas que dura la nota)
    """
    import random

    rng = random.Random(semilla)
    mapa = mapa if mapa is not None else cargar_mapa()
    agenda, usados, ignoradas, desconocidos = [], {}, 0, set()
    fin_activos = []
    for nota in leer_notas(ruta, tempo):
        if canal is not None and nota.canal != canal - 1:
            continue
        tipo = evento_de_nota(nota, mapa)
        if not tipo:
            ignoradas += 1
            continue
        if tipo not in tipos:
            desconocidos.add(tipo)
            continue
        clase = tipos[tipo]
        # algunos eventos "asoman" y no están en su momento fuerte (el "zenit") nada
        # más arrancar, sino a mitad de subir; para esos, la nota marca el zenit, no
        # el arranque, así que el evento se adelanta la mitad de lo que tarda en subir
        retroceso = clase.SUBIR / 2 if getattr(clase, "AJUSTA_CENIT", False) else 0.0
        ini = int(round((nota.inicio + desfase - retroceso) * fps))
        if ini < 0 or (n_frames is not None and ini >= n_frames):
            continue
        fin_activos = [f for f in fin_activos if f > ini]
        if len(fin_activos) >= max_simultaneos:
            continue  # demasiados a la vez: se salta para no frenar el render
        ev = clase(W, H, fps, rng)
        ev.velocidad = nota.velocidad
        ev.mantener = max(1, int(round((nota.fin - nota.inicio) * fps)))
        if hasattr(ev, "ajustar_a_nota"):
            ev.ajustar_a_nota()
        agenda.append((ini, ev))
        fin_activos.append(ini + ev.duracion)
        usados[nota.nombre] = tipo
    if desconocidos:
        print(f"  Aviso: el mapa MIDI usa eventos que no existen: {', '.join(sorted(desconocidos))}. "
              f"Disponibles: {', '.join(tipos)}")
    if ignoradas:
        print(f"  {ignoradas} notas MIDI sin evento asignado (ignoradas)")
    return agenda, usados
