# FictionReaper

Download [Royal Road](https://www.royalroad.com/) fiction chapters as **Markdown** files.

Async-first Python tool with:

- **CLI** (`fictionreaper download <url>`)
- **Small FastAPI server** (`POST /download`)
- **Pydantic** models and **strict typing** (`mypy --strict`)
- Managed with **[uv](https://github.com/astral-sh/uv)**

## Features (v1)

| Input | Behavior |
|-------|----------|
| Fiction homepage URL | Download **all** chapters |
| Chapter URL | Download **that** chapter |

Files land under:

```text
./downloads/<fiction-slug>/0001-chapter-slug.md
./downloads/<fiction-slug>/0002-chapter-slug.md
...
```

Each file has YAML front matter (`title`, `fiction`, `source`, ids) plus a `#` heading and Markdown body.

## Install

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Fluder-Paradyne/FictionReaper.git
cd FictionReaper
uv sync --all-groups
```

## CLI

```bash
# Full fiction
uv run fictionreaper download "https://www.royalroad.com/fiction/21220/mother-of-learning"

# Single chapter
uv run fictionreaper download "https://www.royalroad.com/fiction/21220/mother-of-learning/chapter/301778/1-good-morning-brother"

# Options
uv run fictionreaper download <url> --output-dir ./downloads --delay 1.0
uv run fictionreaper --version
```

`--delay` is the polite pause (seconds) between HTTP requests (default `1.0`).

## API

```bash
uv run uvicorn fictionreaper.api:app --reload --port 8000
```

```bash
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/download \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://www.royalroad.com/fiction/21220/mother-of-learning/chapter/301778/1-good-morning-brother",
    "output_dir": "downloads",
    "delay_seconds": 1.0
  }'
```

OpenAPI docs: `http://127.0.0.1:8000/docs`

## Development

```bash
uv sync --all-groups
uv run pytest
uv run mypy src
uv run ruff check src tests
```

## Project layout

```text
src/fictionreaper/
  models.py      # Pydantic models
  urls.py        # URL classify / normalize
  fetch.py       # httpx.AsyncClient wrapper
  parse.py       # BeautifulSoup → models
  write.py       # Markdown on disk
  pipeline.py    # orchestration
  cli.py         # Typer
  api.py         # FastAPI
```

## Ethics & legal

- For **personal archival / offline reading** of content you are allowed to access.
- Be polite: keep a non-zero `--delay`, don’t hammer the site.
- Respect [Royal Road’s Terms of Service](https://www.royalroad.com/) and copyright. Redistributing scraped novels is not the purpose of this tool.
- Identify your traffic: default User-Agent is `FictionReaper/0.1 (+https://github.com/Fluder-Paradyne/FictionReaper)`.

## License

MIT — see [LICENSE](LICENSE).
