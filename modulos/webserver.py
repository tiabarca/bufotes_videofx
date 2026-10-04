"""
Interfaz web local para generar un episodio sin usar la terminal: arrastras
los archivos, rellenas el formulario y pulsas "Generar vídeo". Sin
dependencias nuevas (solo http.server de la librería estándar).

Pensado para un uso a la vez (herramienta local, no un servicio):

    python ranas.py --webserver
    python ranas.py --webserver --puerto 8080

Cada "Generar vídeo" lanza ranas.py tal cual se lanzaría a mano, como
subproceso, y esta página va enseñando su salida igual que se vería en la
terminal.
"""

import json
import os
import re
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RANAS_PY = os.path.join(RAIZ, "ranas.py")
TRABAJO = os.path.join(RAIZ, "webserver_trabajo")

ESTADO = {"corriendo": False, "log": [], "error": None, "salida": None}
_lock = threading.Lock()
_proceso = [None]


def _tipos_eventos():
    sys.path.insert(0, RAIZ) if RAIZ not in sys.path else None
    import modulos.eventos_extra  # noqa: F401  (registra los eventos nuevos)
    from modulos.eventos import TIPOS
    return sorted(TIPOS)


def _nombre_seguro(nombre):
    nombre = os.path.basename(nombre or "archivo")
    return re.sub(r"[^A-Za-z0-9._-]", "_", nombre) or "archivo"


def _guardar_subida(campo, nombre, cuerpo):
    os.makedirs(TRABAJO, exist_ok=True)
    ruta = os.path.join(TRABAJO, f"{campo}__{_nombre_seguro(nombre)}")
    with open(ruta, "wb") as f:
        f.write(cuerpo)
    return ruta


def _analizar(ruta_a, ruta_b):
    """Mismo cálculo que --analizar, reutilizando audio.py tal cual."""
    from modulos.audio import cargar_audio, diagnostico, nivel_por_fotograma
    aa, ab = cargar_audio(ruta_a), cargar_audio(ruta_b)
    n = min(len(aa), len(ab))
    da, db = nivel_por_fotograma(aa[:n], 24), nivel_por_fotograma(ab[:n], 24)
    ua = diagnostico("A", da, db)
    ub = diagnostico("B", db, da)
    return round(float(ua), 1), round(float(ub), 1)


def _construir_comando(d):
    cmd = [sys.executable, RANAS_PY, "--a", d["a"], "--b", d["b"]]
    if d.get("mezcla"):
        cmd += ["--mezcla", d["mezcla"]]
    os.makedirs(TRABAJO, exist_ok=True)
    salida = os.path.join(TRABAJO, _nombre_seguro(d.get("salida") or "episodio.mp4"))
    cmd += ["-o", salida]
    if d.get("assets"):
        cmd += ["--assets", d["assets"]]
    simples = (
        ("ancho", "--ancho"), ("alto", "--alto"), ("fps", "--fps"), ("duracion", "--duracion"),
        ("sensibilidad", "--sensibilidad"), ("antisangrado", "--antisangrado"),
        ("tamano_ranas", "--tamano-ranas"), ("eventos_cada", "--eventos-cada"),
        ("midi_mapa", "--midi-mapa"), ("midi_desfase", "--midi-desfase"), ("midi_canal", "--midi-canal"),
        ("semilla", "--semilla"), ("titulo_duracion", "--titulo-duracion"),
        ("portada_duracion", "--portada-duracion"), ("crf", "--crf"), ("preset", "--preset"),
    )
    for campo, bandera in simples:
        v = d.get(campo)
        if v not in (None, ""):
            cmd += [bandera, str(v)]
    ua, ub = d.get("umbral_a"), d.get("umbral_b")
    if ua not in (None, "") or ub not in (None, ""):
        cmd += ["--umbral", str(ua if ua not in (None, "") else ub), str(ub if ub not in (None, "") else ua)]
    accs = d.get("accesorios") or ["sombrero", "gafas"]
    cmd += ["--accesorios", accs[0], accs[1]]
    if d.get("titulo"):
        cmd += ["--titulo", d["titulo"]]
    if d.get("sin_logo"):
        cmd.append("--sin-logo")
    if d.get("sin_portada"):
        cmd.append("--sin-portada")
    if d.get("midi"):
        cmd += ["--midi", d["midi"]]
    eventos = d.get("eventos")
    if eventos is not None:
        cmd += ["--eventos"] + list(eventos)
    return cmd, salida


def _lanzar_render(d):
    with _lock:
        if ESTADO["corriendo"]:
            return False
        ESTADO.update(corriendo=True, log=[], error=None, salida=None)

    def _hilo():
        cmd, salida = _construir_comando(d)
        ESTADO["log"].append("$ " + " ".join(cmd))
        try:
            proc = subprocess.Popen(cmd, cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, encoding="utf-8", errors="replace", bufsize=1)
            _proceso[0] = proc
            for linea in proc.stdout:
                ESTADO["log"].append(linea.rstrip("\n"))
            proc.wait()
            if proc.returncode == 0:
                ESTADO["salida"] = salida
            else:
                ESTADO["error"] = f"ranas.py terminó con código {proc.returncode}"
        except Exception as e:
            ESTADO["error"] = str(e)
        finally:
            _proceso[0] = None
            ESTADO["corriendo"] = False

    threading.Thread(target=_hilo, daemon=True).start()
    return True


class Manejador(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _enviar(self, cuerpo, tipo, codigo=200, cabeceras=()):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        for k, v in cabeceras:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, datos, codigo=200):
        self._enviar(json.dumps(datos).encode("utf-8"), "application/json; charset=utf-8", codigo)

    def do_GET(self):
        ruta = urlparse(self.path).path
        if ruta == "/":
            self._enviar(PAGINA.encode("utf-8"), "text/html; charset=utf-8")
        elif ruta == "/tipos":
            self._json({"eventos": _tipos_eventos()})
        elif ruta == "/estado":
            with _lock:
                self._json(dict(ESTADO))
        elif ruta == "/descarga":
            salida = ESTADO.get("salida")
            if not salida or not os.path.exists(salida):
                return self.send_error(404)
            with open(salida, "rb") as f:
                datos = f.read()
            self._enviar(datos, "video/mp4",
                         cabeceras=[("Content-Disposition", f'attachment; filename="{os.path.basename(salida)}"')])
        else:
            self.send_error(404)

    def do_POST(self):
        ruta = urlparse(self.path).path
        largo = int(self.headers.get("Content-Length", 0))
        cuerpo = self.rfile.read(largo) if largo else b""
        if ruta.startswith("/subir/"):
            campo = ruta.split("/")[-1]
            nombre = unquote(self.headers.get("X-Nombre-Archivo", "archivo"))
            try:
                guardada = _guardar_subida(campo, nombre, cuerpo)
                self._json({"ok": True, "ruta": guardada, "nombre": os.path.basename(guardada)})
            except OSError as e:
                self._json({"ok": False, "error": str(e)}, 500)
        elif ruta == "/analizar":
            try:
                d = json.loads(cuerpo or b"{}")
                ua, ub = _analizar(d["a"], d["b"])
                self._json({"ok": True, "umbral_a": ua, "umbral_b": ub})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 400)
        elif ruta == "/render":
            try:
                d = json.loads(cuerpo or b"{}")
                self._json({"ok": _lanzar_render(d)})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 400)
        elif ruta == "/cancelar":
            if _proceso[0]:
                _proceso[0].terminate()
            self._json({"ok": True})
        else:
            self.send_error(404)


PAGINA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bufotes VideoFX</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; max-width: 920px; margin: 2rem auto; padding: 0 1rem; line-height: 1.4; }
  h1 { margin-bottom: .2rem; }
  .sub { opacity: .7; margin-top: 0; }
  fieldset { border: 1px solid #8884; border-radius: 10px; margin: 1.2rem 0; padding: 1rem 1.2rem; }
  legend { font-weight: 600; padding: 0 .4rem; }
  .zonas { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: .8rem; }
  .zona {
    border: 2px dashed #8886; border-radius: 10px; padding: 1.2rem .8rem; text-align: center;
    cursor: pointer; transition: background .15s, border-color .15s; min-height: 90px;
    display: flex; flex-direction: column; justify-content: center; gap: .3rem;
  }
  .zona:hover { background: #8881; }
  .zona.sobre { background: #4a90d922; border-color: #4a90d9; }
  .zona.ok { border-color: #2e9e4f; border-style: solid; }
  .zona .titulo { font-weight: 600; }
  .zona .detalle { font-size: .85em; opacity: .75; word-break: break-all; }
  .zona input { display: none; }
  .fila { display: flex; flex-wrap: wrap; gap: .8rem 1.4rem; align-items: center; margin: .5rem 0; }
  .campo { display: flex; flex-direction: column; gap: .2rem; min-width: 140px; }
  .campo label { font-size: .85em; opacity: .8; }
  input[type=text], input[type=number], select {
    padding: .35rem .5rem; border-radius: 6px; border: 1px solid #8886; background: transparent; color: inherit;
  }
  .switch { display: flex; align-items: center; gap: .5rem; }
  .eventos { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: .3rem .8rem; }
  .eventos label { display: flex; align-items: center; gap: .4rem; font-size: .92em; }
  button.principal {
    font-size: 1.05rem; padding: .7rem 1.6rem; border-radius: 10px; border: none;
    background: #2e9e4f; color: white; cursor: pointer; font-weight: 600;
  }
  button.principal:disabled { opacity: .5; cursor: not-allowed; }
  button.secundaria {
    padding: .5rem 1rem; border-radius: 8px; border: 1px solid #8886; background: transparent; color: inherit; cursor: pointer;
  }
  #panel { display: none; margin-top: 1.2rem; }
  #log {
    background: #0008; color: #ddd; font-family: ui-monospace, monospace; font-size: .85em;
    padding: .8rem; border-radius: 8px; max-height: 260px; overflow-y: auto; white-space: pre-wrap;
  }
  #descarga { display: none; margin-top: .8rem; }
  details summary { cursor: pointer; font-weight: 600; margin-bottom: .5rem; }
</style>
</head>
<body>
<h1>🐸 Bufotes VideoFX</h1>
<p class="sub">Arrastra las pistas, rellena lo que quieras y genera el vídeo.</p>

<fieldset>
  <legend>Archivos</legend>
  <div class="zonas">
    <div class="zona" data-campo="a" data-oblig="1"><div class="titulo">Pista A *</div><div class="detalle">arrastra o haz clic</div><input type="file" accept="audio/*"></div>
    <div class="zona" data-campo="b" data-oblig="1"><div class="titulo">Pista B *</div><div class="detalle">arrastra o haz clic</div><input type="file" accept="audio/*"></div>
    <div class="zona" data-campo="mezcla"><div class="titulo">Mezcla (opcional)</div><div class="detalle">si no, se mezclan A+B</div><input type="file" accept="audio/*"></div>
    <div class="zona" data-campo="midi"><div class="titulo">MIDI (opcional)</div><div class="detalle">.mid de gags</div><input type="file" accept=".mid,.midi"></div>
  </div>
</fieldset>

<fieldset>
  <legend>Título y salida</legend>
  <div class="fila">
    <div class="campo" style="flex:1 1 320px">
      <label>Título de entrada</label>
      <input type="text" id="titulo" placeholder='p. ej. "Bufotes Episodio 94"'>
    </div>
    <div class="campo">
      <label>Nombre del archivo</label>
      <input type="text" id="salida" value="episodio.mp4">
    </div>
  </div>
  <div class="fila">
    <label class="switch"><input type="checkbox" id="sin_logo"> Sin logo</label>
    <label class="switch"><input type="checkbox" id="sin_portada"> Sin portada</label>
  </div>
</fieldset>

<fieldset>
  <legend>Umbral de voz</legend>
  <label class="switch"><input type="checkbox" id="auto_umbral" checked>
    Calcular el umbral automáticamente antes de generar (analiza A y B)</label>
  <div class="fila" style="margin-top:.6rem">
    <div class="campo"><label>Umbral A (dBFS)</label><input type="number" id="umbral_a" step="0.1" placeholder="auto"></div>
    <div class="campo"><label>Umbral B (dBFS)</label><input type="number" id="umbral_b" step="0.1" placeholder="auto"></div>
  </div>
</fieldset>

<fieldset>
  <legend>Eventos</legend>
  <div class="fila">
    <button type="button" class="secundaria" onclick="marcarTodos(true)">Todos</button>
    <button type="button" class="secundaria" onclick="marcarTodos(false)">Ninguno</button>
    <div class="campo"><label>Cada cuántos segundos (al azar)</label><input type="number" id="eventos_cada" value="25"></div>
  </div>
  <div class="eventos" id="eventos"></div>
</fieldset>

<details>
  <summary>Avanzado</summary>
  <fieldset>
    <legend>Ranas</legend>
    <div class="fila">
      <div class="campo"><label>Accesorio A</label>
        <select id="acc_a"><option value="sombrero">sombrero</option><option value="gafas">gafas</option><option value="nada">nada</option></select></div>
      <div class="campo"><label>Accesorio B</label>
        <select id="acc_b"><option value="gafas" selected>gafas</option><option value="sombrero">sombrero</option><option value="nada">nada</option></select></div>
      <div class="campo"><label>Tamaño ranas</label><input type="number" id="tamano_ranas" value="0.8" step="0.05"></div>
      <div class="campo"><label>Carpeta --assets</label><input type="text" id="assets" placeholder="sprites_editables"></div>
    </div>
  </fieldset>
  <fieldset>
    <legend>MIDI</legend>
    <div class="fila">
      <div class="campo"><label>Mapa (--midi-mapa)</label><input type="text" id="midi_mapa" placeholder="midi_mapa.ini"></div>
      <div class="campo"><label>Desfase (s)</label><input type="number" id="midi_desfase" value="0" step="0.1"></div>
      <div class="campo"><label>Canal (1-16)</label><input type="number" id="midi_canal" min="1" max="16"></div>
    </div>
  </fieldset>
  <fieldset>
    <legend>Vídeo</legend>
    <div class="fila">
      <div class="campo"><label>Ancho</label><input type="number" id="ancho" value="1280"></div>
      <div class="campo"><label>Alto</label><input type="number" id="alto" value="720"></div>
      <div class="campo"><label>FPS</label><input type="number" id="fps" value="24"></div>
      <div class="campo"><label>CRF</label><input type="number" id="crf" value="23"></div>
      <div class="campo"><label>Preset x264</label>
        <select id="preset">
          <option>veryfast</option><option>ultrafast</option><option>superfast</option><option>faster</option>
          <option>fast</option><option>medium</option><option>slow</option><option>slower</option><option>veryslow</option>
        </select></div>
      <div class="campo"><label>Duración de prueba (s)</label><input type="number" id="duracion" placeholder="todo"></div>
      <div class="campo"><label>Semilla</label><input type="number" id="semilla" placeholder="al azar"></div>
      <div class="campo"><label>Título: duración (s)</label><input type="number" id="titulo_duracion" value="10"></div>
      <div class="campo"><label>Portada: desvanece (s)</label><input type="number" id="portada_duracion" value="5"></div>
    </div>
  </fieldset>
</details>

<button class="principal" id="generar" onclick="generar()">Generar vídeo</button>

<div id="panel">
  <h3>Progreso</h3>
  <div id="log"></div>
  <div class="fila" style="margin-top:.6rem">
    <button class="secundaria" onclick="cancelar()">Cancelar</button>
  </div>
  <div id="descarga"><a id="enlace_descarga" class="principal" style="text-decoration:none; display:inline-block" href="/descarga">⬇ Descargar vídeo</a></div>
</div>

<script>
const archivos = {a: null, b: null, mezcla: null, midi: null};

function marcarTodos(valor) {
  document.querySelectorAll('#eventos input[type=checkbox]').forEach(c => c.checked = valor);
}

async function cargarTipos() {
  const r = await fetch('/tipos');
  const j = await r.json();
  const cont = document.getElementById('eventos');
  cont.innerHTML = j.eventos.map(nombre =>
    `<label><input type="checkbox" value="${nombre}" checked> ${nombre}</label>`).join('');
}

function estadoZona(zona, clase, detalle) {
  zona.classList.remove('ok', 'sobre');
  if (clase) zona.classList.add(clase);
  if (detalle !== undefined) zona.querySelector('.detalle').textContent = detalle;
}

async function subirArchivo(campo, zona, file) {
  estadoZona(zona, null, 'subiendo ' + file.name + '…');
  try {
    const r = await fetch('/subir/' + campo, {
      method: 'POST',
      headers: {'X-Nombre-Archivo': encodeURIComponent(file.name)},
      body: file
    });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'fallo al subir');
    archivos[campo] = j.ruta;
    estadoZona(zona, 'ok', '✓ ' + j.nombre);
  } catch (e) {
    estadoZona(zona, null, 'error: ' + e.message);
  }
}

function prepararZonas() {
  document.querySelectorAll('.zona').forEach(zona => {
    const campo = zona.dataset.campo;
    const input = zona.querySelector('input[type=file]');
    zona.addEventListener('click', () => input.click());
    input.addEventListener('change', () => { if (input.files[0]) subirArchivo(campo, zona, input.files[0]); });
    zona.addEventListener('dragover', e => { e.preventDefault(); zona.classList.add('sobre'); });
    zona.addEventListener('dragleave', () => zona.classList.remove('sobre'));
    zona.addEventListener('drop', e => {
      e.preventDefault();
      zona.classList.remove('sobre');
      const file = e.dataTransfer.files[0];
      if (file) subirArchivo(campo, zona, file);
    });
  });
}

function num(id) {
  const v = document.getElementById(id).value;
  return v === '' ? null : v;
}

function recogerFormulario(umbralA, umbralB) {
  const eventos = [...document.querySelectorAll('#eventos input:checked')].map(c => c.value);
  return {
    a: archivos.a, b: archivos.b, mezcla: archivos.mezcla, midi: archivos.midi,
    titulo: document.getElementById('titulo').value || null,
    salida: document.getElementById('salida').value || 'episodio.mp4',
    sin_logo: document.getElementById('sin_logo').checked,
    sin_portada: document.getElementById('sin_portada').checked,
    umbral_a: umbralA, umbral_b: umbralB,
    eventos: eventos,
    eventos_cada: num('eventos_cada'),
    accesorios: [document.getElementById('acc_a').value, document.getElementById('acc_b').value],
    tamano_ranas: num('tamano_ranas'),
    assets: document.getElementById('assets').value || null,
    midi_mapa: document.getElementById('midi_mapa').value || null,
    midi_desfase: num('midi_desfase'),
    midi_canal: num('midi_canal'),
    ancho: num('ancho'), alto: num('alto'), fps: num('fps'), crf: num('crf'),
    preset: document.getElementById('preset').value,
    duracion: num('duracion'), semilla: num('semilla'),
    titulo_duracion: num('titulo_duracion'), portada_duracion: num('portada_duracion'),
  };
}

function anadirLog(linea) {
  const log = document.getElementById('log');
  log.textContent += linea + '\n';
  log.scrollTop = log.scrollHeight;
}

async function generar() {
  if (!archivos.a || !archivos.b) { alert('Hace falta subir la pista A y la B.'); return; }
  const boton = document.getElementById('generar');
  boton.disabled = true;
  document.getElementById('panel').style.display = 'block';
  document.getElementById('descarga').style.display = 'none';
  document.getElementById('log').textContent = '';

  let umbralA = num('umbral_a'), umbralB = num('umbral_b');
  if (document.getElementById('auto_umbral').checked) {
    anadirLog('Calculando umbral…');
    try {
      const r = await fetch('/analizar', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({a: archivos.a, b: archivos.b})
      });
      const j = await r.json();
      if (!j.ok) throw new Error(j.error);
      umbralA = j.umbral_a; umbralB = j.umbral_b;
      document.getElementById('umbral_a').value = umbralA;
      document.getElementById('umbral_b').value = umbralB;
      anadirLog(`Umbral calculado: A=${umbralA}  B=${umbralB}`);
    } catch (e) {
      anadirLog('Error calculando el umbral: ' + e.message);
      boton.disabled = false;
      return;
    }
  }

  const r = await fetch('/render', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(recogerFormulario(umbralA, umbralB))
  });
  const j = await r.json();
  if (!j.ok) { anadirLog('Ya hay un vídeo generándose.'); boton.disabled = false; return; }
  sondear(boton);
}

function sondear(boton) {
  const iv = setInterval(async () => {
    const r = await fetch('/estado');
    const j = await r.json();
    document.getElementById('log').textContent = j.log.join('\n');
    document.getElementById('log').scrollTop = 1e9;
    if (!j.corriendo) {
      clearInterval(iv);
      boton.disabled = false;
      if (j.error) anadirLog('❌ ' + j.error);
      else if (j.salida) document.getElementById('descarga').style.display = 'block';
    }
  }, 1500);
}

async function cancelar() {
  await fetch('/cancelar', {method: 'POST'});
}

prepararZonas();
cargarTipos();
</script>
</body>
</html>
"""


def arrancar(puerto=8080):
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    url = f"http://127.0.0.1:{puerto}/"
    print(f"Servidor web en {url} (Ctrl+C para pararlo)")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nParado.")
