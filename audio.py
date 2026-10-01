"""Análisis de audio: niveles por fotograma y estado de la boca de cada rana."""

import os
import shutil
import subprocess

import numpy as np


def buscar_ffmpeg():
    """ffmpeg junto al script (útil en Windows) o, si no, el del PATH."""
    carpeta = os.path.dirname(os.path.abspath(__file__))
    for nombre in ("ffmpeg.exe", "ffmpeg"):
        ruta = os.path.join(carpeta, nombre)
        if os.path.isfile(ruta):
            return ruta
    return shutil.which("ffmpeg")


FFMPEG = buscar_ffmpeg() or "ffmpeg"

SR = 16000  # frecuencia de análisis (no afecta al audio final)


def cargar_audio(ruta, duracion=None):
    """Decodifica cualquier formato con ffmpeg a mono float32 a 16 kHz."""
    cmd = [FFMPEG, "-v", "error", "-i", ruta]
    if duracion:
        cmd += ["-t", str(duracion)]
    cmd += ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    datos = subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout
    return np.frombuffer(datos, dtype=np.float32)


def nivel_por_fotograma(audio, fps):
    """Nivel RMS en dB por fotograma de vídeo."""
    hop = SR / fps
    n = int(len(audio) / hop)
    idx = (np.arange(n) * hop).astype(int)
    win = int(hop * 1.5)  # ventana algo mayor que el fotograma: más suave
    cs = np.concatenate([[0.0], np.cumsum(audio.astype(np.float64) ** 2)])
    ini = np.clip(idx - win // 4, 0, len(audio))
    fin = np.clip(ini + win, 0, len(audio))
    energia = (cs[fin] - cs[ini]) / np.maximum(fin - ini, 1)
    return 10 * np.log10(energia + 1e-10)


def tasa_cruces_por_fotograma(audio, fps):
    """
    Tasa de cruces por cero por fotograma: alta en consonantes sordas/fricativas
    (s, f, t, k...), baja en vocales (dominadas por el tono, más periódicas).
    Sirve para distinguir una boca "oclusiva" de una vocal abierta.
    """
    hop = SR / fps
    n = int(len(audio) / hop)
    idx = (np.arange(n) * hop).astype(int)
    win = int(hop * 1.5)
    signo = (audio >= 0).astype(np.int8)
    cambios = np.concatenate([[0], np.abs(np.diff(signo))])
    cs = np.concatenate([[0], np.cumsum(cambios)])
    ini = np.clip(idx - win // 4, 0, len(audio))
    fin = np.clip(ini + win, 0, len(audio))
    return (cs[fin] - cs[ini]) / np.maximum(fin - ini, 1)


def centroide_por_fotograma(audio, fps):
    """
    Centro de masa espectral por fotograma, normalizado 0..1 según el propio
    rango de la pista (grave→agudo). Es una aproximación muy simple al "color"
    de la vocal (redonda/grave como o-u frente a ancha/aguda como i-e), no un
    detector de vocales real: no hay análisis de formantes.
    """
    hop = SR / fps
    n = int(len(audio) / hop)
    win = int(hop * 1.5)
    if n == 0 or win < 4:
        return np.zeros(n)
    freqs = np.fft.rfftfreq(win, d=1.0 / SR)
    ventana = np.hanning(win)
    centroide = np.zeros(n)
    for i in range(n):
        ini = max(0, int(i * hop - win // 4))
        fin = min(len(audio), ini + win)
        seg = audio[ini:fin]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        espectro = np.abs(np.fft.rfft(seg * ventana))
        total = espectro.sum()
        centroide[i] = (freqs * espectro).sum() / total if total > 1e-9 else 0.0
    lo, hi = np.percentile(centroide, 10), np.percentile(centroide, 90)
    return np.clip((centroide - lo) / max(hi - lo, 1.0), 0.0, 1.0)


def estimar_atenuacion(db_propio, db_otro):
    """
    Cuántos dB más bajo llega el compañero a este micro (sangrado).
    Se mide en los fotogramas donde el otro habla fuerte: en la mayoría este
    micro solo capta sangrado, así que un percentil alto de la diferencia la estima.
    """
    fuerte = db_otro > np.percentile(db_otro, 80)
    if fuerte.sum() < 10:
        return 20.0
    return float(np.clip(np.percentile((db_otro - db_propio)[fuerte], 75), 6.0, 40.0))


def estados_boca(db_propio, db_otro, zcr_propio, centro_propio, sensibilidad=0.0, antisangrado=None, umbral=None):
    """
    Devuelve el estado de la boca por fotograma:
      0 cerrada
      1 vocal pequeña y redonda (grave: o, u)      2 vocal pequeña y ancha (aguda: a, e, i)
      3 vocal grande y redonda                      4 vocal grande y ancha
      5 oclusiva (consonante tipo p/t/k/b/d/g...)
      6 grito (muy fuerte: abre mucho y hace saltar a la rana)
    "Redonda/ancha" es solo una aproximación por el color espectral (centro de
    masa agudo/grave), no una detección de vocales real.
    - Umbrales relativos al suelo de ruido y al nivel de voz de cada pista.
    - Anti-sangrado: si este micro solo suena lo que tocaría por captar al
      compañero (nivel del otro − atenuación, + 4 dB de margen), la boca se
      queda cerrada. Si suena claramente más, es voz propia aunque el otro
      también hable: así funcionan los solapamientos, incluso en voz baja.
      antisangrado=None la estima sola; un número fija la atenuación en dB.
    - umbral: nivel mínimo absoluto en dBFS. Por debajo, la boca nunca se abre,
      pase lo que pase con los umbrales automáticos.
    """
    suelo = np.percentile(db_propio, 15)
    voz = np.percentile(db_propio, 95)
    rango = max(voz - suelo, 6.0)
    u_abre = suelo + rango * 0.35 - sensibilidad
    u_cierra = suelo + rango * 0.25 - sensibilidad  # histéresis
    u_ancha = suelo + rango * 0.70 - sensibilidad
    u_grito = voz + 4.0 - sensibilidad
    if umbral is not None:
        u_abre = max(u_abre, umbral)
        u_cierra = max(u_cierra, umbral - 2.0)
        u_ancha = max(u_ancha, umbral + 6.0)
        u_grito = max(u_grito, umbral + 14.0)

    aten = estimar_atenuacion(db_propio, db_otro) if antisangrado is None else antisangrado
    margen = 4.0

    # un solo fotograma de ruido no debe bastar para que "parezca" una
    # consonante o cambie el color de vocal: se suavizan ambas señales antes
    # de decidir la forma, si no la boca parpadea en cada mínimo cambio
    ventana = np.ones(5) / 5
    zcr_propio = np.convolve(zcr_propio, ventana, mode="same")
    centro_propio = np.convolve(centro_propio, ventana, mode="same")
    u_zcr = np.percentile(zcr_propio, 85)  # solo picos de verdad claros: consonante

    estados = np.zeros(len(db_propio), dtype=np.int8)
    hablando = False
    for i, d in enumerate(db_propio):
        sangrado = d < db_otro[i] - aten + margen
        if hablando:
            hablando = d > u_cierra and not sangrado
        else:
            hablando = d > u_abre and not sangrado
        if hablando:
            if d > u_grito:
                estados[i] = 6
            elif zcr_propio[i] > u_zcr:
                estados[i] = 5
            else:
                grande = d > u_ancha
                ancha = centro_propio[i] > 0.5
                estados[i] = (4 if ancha else 3) if grande else (2 if ancha else 1)

    # quitar parpadeos de boca de 1 fotograma
    for i in range(1, len(estados) - 1):
        if estados[i - 1] == estados[i + 1] != estados[i]:
            estados[i] = estados[i - 1]
    return estados


def diagnostico(nombre, db_propio, db_otro):
    """Imprime los niveles de una pista para elegir --umbral a ojo."""
    otro_fuerte = db_otro > np.percentile(db_otro, 80)
    # cuando el otro habla fuerte y yo no: lo que suena es sangrado
    solo_otro = otro_fuerte & (db_propio < db_otro - 6)
    sangr = db_propio[solo_otro] if solo_otro.sum() > 10 else np.array([np.nan])
    suelo = np.percentile(db_propio, 15)
    voz = db_propio[db_propio > np.nanpercentile(sangr, 95) + 3] if solo_otro.sum() > 10 else db_propio
    voz_med = np.percentile(voz, 50) if len(voz) else np.nan
    recomendado = np.nanpercentile(sangr, 95) + 3
    print(f"  Pista {nombre}: silencio ≈ {suelo:.0f} dBFS · sangrado del otro ≈ "
          f"{np.nanpercentile(sangr, 50):.0f} (picos {np.nanpercentile(sangr, 95):.0f}) · "
          f"voz propia ≈ {voz_med:.0f} dBFS → --umbral sugerido ≈ {recomendado:.0f}")
    return recomendado
