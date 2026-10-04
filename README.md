# Bufotes VideoFX 🐸

Generador de vídeo para **[Bufotes Balearicus](https://bufotesbalearicus.cat)**, *un podcast illenc*.

## El podcast

Bufotes Balearicus es un podcast de humor en mallorquín: tertulia improvisada entre dos voces sobre actualidad, anécdotas y cultura de las islas, con secciones fijas como las noticias inventadas de *Bufota Today* y los patrocinios en clave de cachondeo. Lleva más de 90 episodios repartidos en tres temporadas.

El nombre viene del *calàpet* (*Bufotes balearicus*), el sapo verde balear. Por eso, en el vídeo, los presentadores son dos ranas.

- 🌐 Web: [bufotesbalearicus.cat](https://bufotesbalearicus.cat)
- 🎧 Spotify: [Bufotes Balearicus](https://open.spotify.com/show/6zZ1yL499upJGVj8QRU9VT)
- 🐦 X: [@BufotesPodcast](https://x.com/BufotesPodcast)

## Qué hace este proyecto

Convierte cada episodio, grabado en dos pistas, en un vídeo en el que dos calàpets hablan en un estanque de la Serra de Tramuntana, con una possessió al fondo. Cada uno mueve la boca con su propia pista. De vez en cuando pasan cosas: un tractor por el camí, un porc negre que asoma la cabeza y se esconde, dos pájaros, un gusano y un rebaño de ovejas pasturando con un perro que las persigue. Las ranas se giran para mirarlos.

Todo se genera en local con Python y ffmpeg, sin IA ni servicios de pago. Un episodio de 30 minutos tarda unos pocos minutos en renderizarse.

| Rana | Pista | Accesorio |
|---|---|---|
| Izquierda | `A` | sombrero de copa |
| Derecha | `B` | gafas redondas |

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
| `--midi gags.mid` | Pista MIDI: cada nota lanza un evento en su instante exacto, además de los aleatorios (ver [Eventos desde una pista MIDI](#eventos-desde-una-pista-midi)). |
| `--midi-mapa otro.ini` | Mapa nota → evento. Por defecto, `midi_mapa.ini` junto a `ranas.py`. |
| `--midi-desfase -0.5` | Segundos a sumar a las notas MIDI (negativo = antes). |
| `--midi-canal 10` | Usar solo las notas de ese canal MIDI. |
| `--semilla 42` | Repite exactamente el mismo orden de eventos. |
| `--accesorios sombrero gafas` | Accesorio de cada rana: `sombrero`, `gafas` o `nada`. |
| `--tamano-ranas 0.8` | Tamaño de las ranas. |
| `--titulo "Bufotes Episodio 94"` | Título de entrada: aparece justo tras la portada, con la tipografía del logo. |
| `--titulo-duracion 10` | Cuánto dura en pantalla el título de entrada. |
| `--sin-logo` | No poner el logo (`media/logo.png`) en la esquina superior izquierda. |
| `--sin-portada` | No abrir con la portada (`media/portada.jpeg`) solapada sobre el arranque. |
| `--portada-duracion 5` | Cuánto tarda la portada en desvanecerse hacia la escena, al principio. |
| `--sensibilidad`, `--antisangrado` | Ajuste fino de la detección de voz. |
| `--ancho`, `--alto`, `--fps`, `--crf` | Resolución, fotogramas por segundo y calidad del vídeo. |

Las tres pistas tienen que empezar en el mismo instante. Si el máster lleva una intro antes de que empecéis a hablar, A y B necesitan el mismo silencio al principio.

## Estructura

```
ranas.py        línea de comandos y render (envía los fotogramas a ffmpeg)
audio.py        niveles por fotograma, umbrales, anti-sangrado entre micros
escena.py       fondo: montañas, marjades con olivos, possessió, estanque
personajes.py   las dos ranas (bocas, parpadeo, mirada, sombrero, gafas)
eventos.py      tractor, cerdo, pájaros, gusano, ovejas, xeremiers, bronca y la programación aleatoria
eventos_extra.py  ocho eventos más (se registran solos al importar el módulo)
midi.py         lector de archivos .mid y del mapa nota → evento (midi_mapa.ini)
overlay.py      logo, portada de entrada y título (media/logo.png, media/portada.jpeg, media/fuentes/)
```

### Logo, portada y título de entrada

El vídeo abre con la portada de `media/portada.jpeg` a pantalla completa
(ya viene a 16:9, no se recorta ni se deforma), que se desvanece hacia la
escena en los últimos segundos de `--portada-duracion` (5 s por defecto;
`--sin-portada` la quita). El logo de `media/logo.png` sale siempre en la
esquina superior izquierda, por debajo de la portada (`--sin-logo` lo
quita). El título de `--titulo` aparece justo cuando acaba la portada, con
la misma tipografía de marcador que el logo y la portada (Permanent
Marker, en `media/fuentes/`): se queda `--titulo-duracion` segundos (10 s
por defecto) y se desvanece. Si el texto no cabe en 2 líneas, la letra se
encoge sola hasta que quepa.

### Añadir un evento nuevo

En `eventos.py` (o en `eventos_extra.py`, ver abajo), crea una clase que herede de `Evento` con:
- `capa`: `"fondo"` (detrás de las ranas) o `"frente"` (delante)
- `duracion`: en fotogramas
- `sprites(t)`: devuelve una lista de `(imagen, x, y)` para el fotograma `t`
- `x_interes(t)`: hacia dónde miran las ranas

Después regístrala en el diccionario `TIPOS`. Aparecerá automáticamente en `--eventos`.

Opcionalmente, un evento puede definir también:
- `afecta_rana(t)` → `{indice_rana: {"bote": n, "ojos": bool}}`: para que ese fotograma le imponga a una rana en concreto un bote mínimo y/o los ojos cerrados (independientemente de su parpadeo normal).
- `viento(t)` → `{"izq"|"der": empuje en px}`: para doblar puntualmente las cañas del estanque de ese lado (ver `Pedo` en `eventos_extra.py`).

## Eventos desde una pista MIDI

Los eventos aleatorios siguen saliendo como siempre, y además puedes decidir tú cuándo pasa algo concreto. En el DAW, añade una pista MIDI encima del podcast, pon una nota donde quieras un gag y expórtala como `.mid` desde el inicio de la sesión:

```
python ranas.py --a audio/A.mp3 --b audio/B.mp3 --mezcla audio/master.mp3 --midi audio/gags.mid -o episodio.mp4
```

### Qué nota lanza cada evento: `midi_mapa.ini`

Está en la carpeta del proyecto y se carga solo. Cada línea es un evento con las notas que lo lanzan, separadas por comas:

```ini
cerdo_asoma = Do, 61      # cualquier Do, y también la nota 61
motocultor  = Sol2        # solo el Sol de la octava 2
tractor     = Sol         # el resto de Soles
pedo        = nada        # el pedo no se lanza desde MIDI (pero sigue saliendo al azar)
```

- Valen nombres latinos o ingleses (Do/C, Re#/D#, Sib/Bb), con o sin octava (C3 = nota 60), y números de nota MIDI.
- Si una tecla encaja en varias líneas, gana la más concreta: número > nota con octava > nota sin octava.
- Las notas que no aparecen en ninguna línea no hacen nada.
- Para usar otro mapa en un episodio concreto, añade `--midi-mapa otro.ini`.

### Más opciones

- La **fuerza de la nota** (velocity) cambia el tamaño o la intensidad del evento: un cerdo más grande, un grillo que salta más alto…
- Los eventos que **asoman** (cerdo_asoma, rana_guapa, muchedumbre, asnos, bombilla) se quedan en pantalla mientras dure la nota.
- Pueden coincidir varios eventos a la vez (de la agenda aleatoria y del MIDI); las ranas miran al que haya empezado más recientemente.
- El MIDI se suma a los eventos aleatorios. Si en un episodio quieres solo los del MIDI, añade `--eventos-cada 0`.
- `--midi-desfase -0.5` adelanta todas las notas medio segundo, por si el MIDI no empieza a la vez que el audio.
- `--midi-canal 10` usa solo las notas de ese canal.

### Lista de eventos

| Evento | Qué pasa | Dónde |
|---|---|---|
| `tractor` | tractor rojo con pagès, ruedas girando y humo | camí del fondo |
| `motocultor` | pagès con motocultor, lento y echando muchísimo humo negro | camí del fondo |
| `cerdo` | el porc negre pasea con una muchedumbre de payeses detrás, cuchillo y olla en alto | camí del fondo |
| `pajaros` | dos pájaros aleteando | cielo |
| `gusano` | se arrastra ondulando hacia la rana más cercana; se lo come de un lengüetazo | delante |
| `mosquito` | vuela errático por delante; la rana hacia la que va se lo come de un lengüetazo | delante |
| `ovejas` | rebaño pasturando con un perro pastor que lo persigue | camí del fondo |
| `xeremiers` | xeremier y flabiolaire tocando, con una pareja de ball de bot | camí del fondo |
| `bronca` | al pagès le gritan desde casa: sale por la puerta y su mujer le riñe desde la ventana con un palo. Solapable: puede coincidir con cualquier otro evento | junto a la possessió |
| `grillo` | cruza a saltos | delante |
| `cerdo_asoma` | el cerdo saca la cabeza por abajo, husmea y parpadea | borde inferior |
| `rana_guapa` | rana con pintalabios, pestañas y lazo; sube del estanque, guiña un ojo y lanza un beso con corazones | estanque, entre las ranas |
| `muchedumbre` | público aplaudiendo | borde inferior |
| `asnos` | dos burros asoman por los lados y se ríen ("IA-IA!") | laterales |
| `bombilla` | baja colgada de un cable, chisporrotea, se enciende y sube | arriba |
| `pedo` | una de las dos ranas (al azar) se tira un pedo: le sale un chorro de humo verdoso por detrás que se expande y se disipa, con "PRRRT!" y líneas de peste. La rana da un bote y cierra los ojos, y la ráfaga dobla las cañas de su lado del estanque, que vuelven oscilando | junto a la rana |

### La boca

Además de abrirse más o menos fuerte, la boca distingue (de forma aproximada,
sin analizar formantes de verdad) entre vocales "redondas" (graves, tipo o/u)
y "anchas" (agudas, tipo a/e/i) por el color espectral, detecta consonantes
oclusivas (p/t/k/b/d/g...) por la tasa de cruces por cero, y tiene un estado
de grito para los picos más fuertes que además hace saltar más a la rana:

```
0 cerrada · 1 vocal pequeña redonda · 2 vocal pequeña ancha
3 vocal grande redonda · 4 vocal grande ancha · 5 oclusiva · 6 grito
```

### Gráficos propios

Las ranas se dibujan siempre por código: es lo que les da la mirada (giran
los ojos y el sombrero hacia donde miran, se miran entre ellas o miran lo
que pasa por la escena). Un PNG fijo las dejaría siempre mirando de frente,
así que no son editables como imagen.

Lo que sí es sustituible por PNG son el fondo y los personajes que pasan por
la escena (tractor, cerdo, payeses, pájaros, gusano, mosquito, ovejas,
perro, xeremiers...). Con `--assets carpeta`:

- `carpeta/fondo.png` sustituye el fondo dibujado por código.
- `carpeta/eventos/{nombre}_{N}.png` sustituye el fotograma N de ese
  personaje (p. ej. `tractor_0.png` .. `tractor_7.png`); si falta alguno,
  ese fotograma en concreto se sigue dibujando por código, así que no hace
  falta aportar el juego completo. Cada PNG puede tener cualquier
  resolución, se reescala solo. El humo del tractor no es sustituible (es
  una mancha translúcida, no un personaje).

**`exportar_sprites.py`** saca la plantilla de todos esos personajes a PNG de
partida, listos para retocar en un editor de imagen:

```
python exportar_sprites.py --salida sprites_editables
# edita los PNG de sprites_editables/eventos/...
python ranas.py --a A.mp3 --b B.mp3 --assets sprites_editables ...
```

## Ideas para una v2

- **Vocales reales por transcripción**: en vez de aproximar la vocal por color
  espectral (ver "La boca" más arriba), mandar cada pista a una API de
  transcripción (speech-to-text) y usar el texto/fonemas con sus tiempos para
  saber qué vocal toca en cada instante. Requeriría conexión a internet y una
  clave de API (deja de ser 100% local y gratis, que es la gracia actual del
  proyecto), pero la sincronía boca-fonema sería mucho más precisa.

## Licencia

[MIT](LICENSE)
