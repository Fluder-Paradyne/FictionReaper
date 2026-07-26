# FictionReaper v1 Implementation Plan

> Implemented inline in the same session as the design.

**Goal:** Ship async Royal Road → Markdown scraper (CLI + FastAPI), fully tested, public repo.

**Architecture:** Shared async core; Typer CLI; FastAPI thin wrapper; uv-managed.

**Tech Stack:** Python 3.12+, httpx, BeautifulSoup/lxml, Pydantic v2, Typer, FastAPI, pytest/respx/mypy/ruff.

## Tasks (completed)

- [x] Scaffold uv package + pyproject tooling
- [x] Models, exceptions, URL resolver + tests
- [x] Fetch, parse, write, pipeline + tests (mocked HTTP)
- [x] CLI + API + tests
- [x] README, LICENSE, design doc
- [x] Public GitHub repository
