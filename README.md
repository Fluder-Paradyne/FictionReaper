# FictionReaper

Download [Royal Road](https://www.royalroad.com/) fiction as **Markdown** and/or **EPUB**.

Works on **macOS** and **Linux** (Python 3.12+). Ships a CLI and a small HTTP API.

## Install (end users)

Pick one. All put a `fictionreaper` command on your `PATH`.

### Option A — uv tool (recommended)

Install [uv](https://docs.astral.sh/uv/), then:

```bash
uv tool install git+https://github.com/Fluder-Paradyne/FictionReaper.git
fictionreaper --version
```

Upgrade later:

```bash
uv tool upgrade fictionreaper
# or reinstall from git tip:
uv tool install --force git+https://github.com/Fluder-Paradyne/FictionReaper.git
```

### Option B — pipx

```bash
pipx install git+https://github.com/Fluder-Paradyne/FictionReaper.git
fictionreaper --version
```

### Option C — pip (venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/Fluder-Paradyne/FictionReaper.git"
fictionreaper --version
```

### Option D — PyPI (after first publish)

```bash
pip install fictionreaper
# or:  uv tool install fictionreaper
# or:  pipx install fictionreaper
```

Publishing notes for maintainers: [docs/PUBLISHING.md](docs/PUBLISHING.md).

### Requirements

| | |
|--|--|
| OS | macOS or Linux |
| Python | **3.12+** (3.13 supported) |
| Network | outbound HTTPS to `royalroad.com` / CDN |

Native wheels for dependencies (`lxml`, etc.) are published for common Mac/Linux platforms; a normal install does not need a compiler in most cases.

## Quick start

```bash
# One chapter → Markdown + EPUB (default)
fictionreaper download \
  "https://www.royalroad.com/fiction/21220/mother-of-learning/chapter/301778/1-good-morning-brother"

# Whole fiction (many chapters — be polite with --delay)
fictionreaper download \
  "https://www.royalroad.com/fiction/21220/mother-of-learning" \
  --delay 1.0

# Formats
fictionreaper download "<url>" --format markdown
fictionreaper download "<url>" --format epub
fictionreaper download "<url>" --format markdown,epub
fictionreaper download "<url>" -f markdown -f epub

# Output directory
fictionreaper download "<url>" --output-dir ~/Books/rr
```

Output layout:

```text
downloads/<fiction-slug>/
  0001-chapter-slug.md
  0002-chapter-slug.md
  ...
  <fiction-slug>.epub
```

## HTTP API

```bash
fictionreaper serve --host 127.0.0.1 --port 8000
# docs: http://127.0.0.1:8000/docs
```

```bash
curl -sS -X POST 'http://127.0.0.1:8000/download' \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://www.royalroad.com/fiction/21220/mother-of-learning/chapter/301778/1-good-morning-brother",
    "output_dir": "downloads",
    "delay_seconds": 1.0,
    "formats": ["markdown", "epub"]
  }'
```

## Development

```bash
git clone https://github.com/Fluder-Paradyne/FictionReaper.git
cd FictionReaper
uv sync --all-groups
uv run pytest
uv run mypy src
uv run ruff check src tests
uv build
```

## Ethics & legal

- For **personal archival / offline reading** of content you are allowed to access.
- Be polite: keep a non-zero `--delay`, don’t hammer the site.
- Respect [Royal Road’s Terms of Service](https://www.royalroad.com/) and copyright.
- Default User-Agent: `FictionReaper/0.1 (+https://github.com/Fluder-Paradyne/FictionReaper)`.

## License

MIT — see [LICENSE](LICENSE).
