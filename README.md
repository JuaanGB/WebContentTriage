# Web Content Triage

Scraper y clasificador de posts de noticias técnicas a través de criterios configurables.

## Enfoque híbrido

1. **Keywords** filtran rápido con pesos por posición (título ×3, headings ×2, párrafos ×1)
2. **LLM (opcional)** refina posts con score ≥ umbral configurable vía LLM consumidos a través de APIs. Para la elaboración de este proyecto se utilizó OpenRouter API.
3. **Caché** evita llamadas repetidas al LLM, ahorrando dinero y tiempo

## Estructura

```
WebContentTriage/
├── main.py                  # Punto de entrada
├── data/
│   ├── keywords.csv         # Keywords de ejemplo
│   └── cache.example.csv    # Ejemplo de formato de caché de LLM
├── src/classifier/
│   ├── cli.py               # Argumentos CLI
│   ├── scraper.py           # Scraper genérico con regex
│   ├── text_extractor.py    # Extracción de texto semántico (h1-h6, p)
│   ├── classifier.py        # Clasificación por keywords
│   ├── llm_classifier.py    # Refinado con LLM vía OpenRouter
│   ├── cache.py             # Gestión de caché LLM
│   └── output.py            # CSV/JSON/pretty print
├── venv/
└── README.md
```

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuración del LLM (opcional)

Para usar el refinado por LLM, crea un archivo `.env`:

```bash
cp .env.example .env
# Editar .env con tu API key de OpenRouter
```

```env
OPENROUTER_API_KEY=sk-or-v1-...
```

Obtén tu key en [openrouter.ai/keys](https://openrouter.ai/keys).

## Uso

### Solo keywords (rápido, sin coste)

```bash
python main.py --keywords data/keywords.csv --max-posts 30
```

### Híbrido: keywords + LLM para posts con score ≥ 5

```bash
python main.py --keywords data/keywords.csv --llm --llm-threshold 5 --max-posts 30
```

Salida:

```
  [página 1/1] https://news.ycombinator.com/
    → 30 posts
  [1/30] Create custom games without coding on Playground... → LLM (Sí, 88/100, 940tk) ✅ score=13
  [2/30] GitHub - zerobrewhq/zerobrew: An up to 100x*... → LLM (No, 15/100, 1012tk) ❌ score=25
  ...

30 posts | 12 relevantes | 18 no relevantes
```

### Guardar en CSV (abre en Excel)

```bash
python main.py --keywords data/keywords.csv --llm --max-posts 50 -o resultados.csv
```

Columnas: `score`, `relevante`, `titulo`, `url`, `keywords`, `title_matches`, `heading_matches`, `paragraph_matches`, `llm_score`, `llm_razon`, `llm_tokens`

Ordenado por score decreciente.

## Cómo funciona la caché

La primera vez que evalúas un post con el LLM, el veredicto se guarda en `data/cache.csv`:

```csv
url,titulo,veredicto
https://example.com/post,Post Title,Sí
```

En siguientes ejecuciones, si la URL ya está en caché, se reutiliza el veredicto sin llamar al LLM:

```
  [2/30] Create custom games without coding on Playground... → cache (Sí, caché) ✅ score=13
```

Esto ahorra dinero y tiempo. La caché crece automáticamente con cada nueva URL evaluada.

El fichero `cache.example.csv` es un fichero de ejemplo que ilustra el formato de la caché.

## Argumentos

| Argumento              | Descripción                                         | Default    |
| ---------------------- | --------------------------------------------------- | ---------- |
| `--keywords FILE`      | CSV con grupos de keywords                          | -          |
| `--max-posts N`        | Máximo de posts a procesar                          | Sin límite |
| `--pages N`            | Páginas a scrapear                                  | 1          |
| `--min-score N`        | Score mínimo para considerar relevante              | 2          |
| `--title-weight N`     | Multiplicador para coincidencias en título          | 3          |
| `--heading-weight N`   | Multiplicador para coincidencias en headings        | 2          |
| `--paragraph-weight N` | Multiplicador para coincidencias en párrafos        | 1          |
| `--llm`                | Activar refinado con LLM vía OpenRouter             | False      |
| `--llm-threshold N`    | Score mínimo para enviar post al LLM                | 5          |
| `--no-extract-text`    | No descargar páginas, usar solo títulos del scraper | False      |
| `-o FILE`              | Guardar resultados (`.csv` o `.json`)               | -          |
| `--verbose`            | Mostrar configuración detallada                     | False      |
| `--dry-run`            | Mostrar configuración sin ejecutar                  | False      |

## Sistema de pesos

| Ubicación       | Peso | Razón                    |
| --------------- | ---- | ------------------------ |
| Título del post | ×3   | Indica tema central      |
| Headings h1-h6  | ×2   | Estructura del contenido |
| Párrafos        | ×1   | Menciones generales      |

Un post necesita score ≥ `--min-score` para considerarse relevante por keywords.

Si `--llm` está activo, los posts con score ≥ `--llm-threshold` se envían al LLM para decisión final. El veredicto del LLM sobreescribe al de keywords.

## Keywords

El archivo `data/keywords.csv` contiene los términos que definen qué es relevante para la búsqueda. Están organizados en grupos de sinónimos (una línea = un grupo).

**Limitaciones conocidas:**

- Requiere mantenimiento manual: nuevas juegos, consolas y términos emergen constantemente o se quiere ampliar la búsqueda a otros temas relacionados.
- Puede generar falsos positivos (ej: "homebrew" como homebrew de consolas frente al gestor de paquetes Homebrew). Para eso está el LLM. Para eso está el LLM.
- No captura sinónimos no listados (ej: "cheats" frente a "exploits").

**Formato del CSV:**

```csv
video game,video games,videogame,videogames,gaming,gamer,gamers
game engine,game development,gamedev,game dev,indie game,indie games
console,consoles,playstation,ps5,xbox,nintendo,switch,steam deck
emulator,emulators,emulation,rom,roms,retro,retrogaming
custom firmware,cfw,homebrew,jailbreak,modding,mod,mods,modder
...
```

Una línea = un grupo de sinónimos. Las palabras de una misma línea se consideran equivalentes y suman para el mismo grupo.

## Scraper genérico

El scraper soporta cualquier sitio mediante patrones regex con marcadores:

- `$URL` — href del enlace
- `$TITLE` — texto del título

Es tarea del programador analizar el sitio web y escribir expresiones regulares que capturen los enlaces a los posts y sus títulos.

### Ejemplo: Hacker News (por defecto)

```bash
python main.py --keywords data/keywords.csv --max-posts 30
```

### Ejemplo: Lobsters

Probado con Lobsters (computing-focused community):

```bash
python main.py \
  --url "https://lobste.rs" \
  --url-pattern '<span role="heading" aria-level="1" class="link h-cite u-repost-of">.*?<a class="u-url" $URL[^>]*>.*?</a>.*?</span>' \
  --title-pattern '<a class="u-url" href="[^"]*"[^>]*$TITLE</a>' \
  --keywords data/keywords.csv \
  --max-posts 10
```

Salida:

```
  [página 1/1] https://lobste.rs
    → 25 posts
  [1/10] The Cuckoo's Egg... → LLM (No, 20/100, 1022tk) ❌ score=2
  [2/10] How to speed up the Rust compiler... → LLM (No, 30/100, 858tk) ❌ score=4
  ...

10 posts | 0 relevantes | 10 no relevantes
```
