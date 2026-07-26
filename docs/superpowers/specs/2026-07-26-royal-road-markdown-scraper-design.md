# FictionReaper v1 Design — Royal Road Markdown Scraper

**Date:** 2026-07-26  
**Status:** Approved for implementation  
**Package manager:** uv  

## Goals

- Given a Royal Road **fiction homepage** or **chapter** URL, download chapter content as **Markdown** files.
- Ship both a **CLI** and a **small FastAPI** server that share one async core.
- Fully tested; Pydantic models; strict typing (`mypy --strict`).
- Public GitHub repository.

## Non-goals (v1)

- EPUB export, authenticated/paywalled content, multi-site support, concurrency beyond sequential polite fetch, GUI.

## Architecture

Async-first pipeline (approach B):

```
URL → resolve → fetch (httpx.AsyncClient) → parse (BS4) → write Markdown
```

Layers:

| Layer | Responsibility |
|-------|----------------|
| Core (`urls`, `fetch`, `parse`, `write`, `pipeline`, `models`) | Pure download logic |
| CLI (`cli.py`) | Typer → `asyncio.run(download(...))` |
| API (`api.py`) | FastAPI `POST /download` → await `download(...)` |

Core must not import FastAPI or Typer.

## URL behavior

- **Fiction** `/fiction/{id}/{slug}` → parse TOC (`tr.chapter-row`), download every chapter.
- **Chapter** `/fiction/{id}/{slug}/chapter/{cid}/{cslug}` → download that chapter; optionally load fiction page for title/author/index.

## Output

- Default base: `./downloads`
- Path: `{output_dir}/{fiction-slug}/{NNNN}-{chapter-slug}.md`
- Content: YAML front matter + `# title` + Markdown body converted from `.chapter-inner.chapter-content`.

## HTTP

- `httpx.AsyncClient`, follow redirects, configurable User-Agent.
- Delay between requests (`delay_seconds`, default `1.0`).
- Errors: `FetchError` on network/HTTP failure.

## API (v1)

- `GET /health` → `{status, version}`
- `POST /download` body: `{url, output_dir?, delay_seconds?}` → metadata + written paths.

## CLI (v1)

```bash
fictionreaper download <url> [--output-dir PATH] [--delay SECONDS]
fictionreaper --version
```

## Testing

- Fixtures: saved RR-shaped HTML under `tests/fixtures/`.
- Unit: urls, parse, write, fetch.
- Integration: pipeline + CLI + API with `respx` mocks (no live network in CI).

## Tooling

- uv for lockfile, venv, run, sync
- pytest + pytest-asyncio + respx
- mypy strict, ruff
- Python ≥ 3.12

## Public repo

- MIT license, README with install/usage and ethics note.
