# Ranas Podcast 🐸

Convierte un podcast grabado en dos pistas en un vídeo de dos ranas que hablan en un estanque de la Serra de Tramuntana, con una possessió al fondo. De vez en cuando pasan cosas: un tractor por el camí, un porc negre que se para a husmear, dos pájaros y un gusano. Las ranas se giran para mirarlos.

Todo se genera en local con Python y ffmpeg, sin IA ni servicios de pago. Un episodio de 30 minutos tarda unos pocos minutos en renderizarse.

## Instalación

1. **Python 3.9 o posterior** (python.org; en Windows marca *Add python.exe to PATH*).
2. **ffmpeg**: en Windows, descarga `ffmpeg-release-essentials.zip` de gyan.dev y copia `bin/ffmpeg.exe` a esta carpeta. En Mac, `brew install ffmpeg`.
3. Abre la carpeta en VS Code y, en la terminal:
   ```
   python -m venv .venv
   .venv\Scripts\activate        (Windows)   ·   source .venv/bin/activate   (Mac/Linux)
   pip install -r requirements.txt
   ```

## Uso rápido en VS Code

Crea una carpeta `audio/` con `A.mp3` (rana izquierda), `B.mp3` (rana derecha) y `master.mp3` (el audio final). Luego, en **Ejecutar y depurar** (F5):

1. **Analizar pistas**: muestra los niveles de cada pista y sugiere un `--umbral`.
2. **Prueba**: renderiza 1 minuto con eventos frecuentes para ver cómo queda.
3. **Episodio completo**: te pide el umbral y el nombre del vídeo.

## Uso desde la terminal

```
python ranas.py --a audio/A.mp3 --b audio/B.mp3 --analizar
python ranas.py --a audio/A.mp3 --b audio/B.mp3 --mezcla audio/master.mp3 --umbral -27 -o episodio.mp4
```

| Opción | Qué hace |
|---|---|
| `--a`, `--b` | Pistas de cada interlocutor. Solo se usan para mover las bocas. Aceptan cualquier formato (mp3, wav, m4a…). |
| `--mezcla` | Audio que lleva el vídeo. Si no se indica, se mezclan A y B. |
| `--umbral -27` | Nivel mínimo en dBFS para que se mueva la boca. Admite uno o dos valores (A B). |
| `--analizar` | Solo analiza y sugiere el umbral. |
| `--duracion 60` | Renderiza solo los primeros N segundos. |
| `--eventos tractor gusano` | Qué puede pasar por la escena. Por defecto, todos. Con `--eventos` sin valores, ninguno. |
| `--eventos-cada 25` | Segundos de media entre eventos (±40 % al azar). |
| `--semilla 42` | Repite exactamente el mismo orden de eventos. |
| `--accesorios sombrero gafas` | Accesorio de cada rana: `sombrero`, `gafas` o `nada`. |
| `--tamano-ranas 0.8` | Tamaño de las ranas. |
| `--sensibilidad`, `--antisangrado` | Ajuste fino de la detección de voz. |
| `--ancho`, `--alto`, `--fps`, `--crf` | Resolución, fotogramas por segundo y calidad del vídeo. |

Las tres pistas tienen que empezar en el mismo instante. Si el máster lleva una intro antes de que empecéis a hablar, A y B necesitan el mismo silencio al principio.

## Estructura

```
ranas.py       línea de comandos y render (envía los fotogramas a ffmpeg)
audio.py       niveles por fotograma, umbrales, anti-sangrado entre micros
escena.py      fondo: montañas, marjades con olivos, possessió, estanque
personajes.py  las dos ranas (bocas, parpadeo, mirada, sombrero, gafas)
eventos.py     tractor, cerdo, pájaros, gusano y la programación aleatoria
```

### Añadir un evento nuevo

En `eventos.py`, crea una clase que herede de `Evento` con:
- `capa`: `"fondo"` (detrás de las ranas) o `"frente"` (delante)
- `duracion`: en fotogramas
- `sprites(t)`: devuelve una lista de `(imagen, x, y)` para el fotograma `t`
- `x_interes(t)`: hacia dónde miran las ranas

Después regístrala en el diccionario `TIPOS`. Aparecerá automáticamente en `--eventos`.

### Gráficos propios

Con `--assets carpeta` se usan tus PNG en lugar de los dibujados por código:
`fondo.png`, `ranaA_boca0.png`, `ranaA_boca1.png`, `ranaA_boca2.png` y `ranaA_ojos_cerrados.png` (capa transparente solo con los párpados), y lo mismo para `ranaB_…`. Los eventos siguen funcionando encima de tu fondo.
