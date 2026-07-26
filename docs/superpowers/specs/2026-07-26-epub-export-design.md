# FictionReaper — EPUB Export Design

**Date:** 2026-07-26  
**Status:** Approved  

## Goals

- On every download, write Markdown chapters **and** one EPUB.
- Embed fiction cover image when available (`og:image` / cover URL).
- Library: **ebooklib**; Markdown→HTML via **markdown** (raw HTML preserved for tables).
- CLI + API report `epub_path`; fully typed and tested.

## Output

```
{output_dir}/{fiction-slug}/
  0001-….md
  …
  {fiction-slug}.epub
```

Single-chapter downloads still produce a one-chapter EPUB in that folder.

## Pipeline

1. Existing download of chapters + Markdown write.
2. Fetch cover bytes if `cover_url` present (same `AsyncFetcher`).
3. `build_epub(meta, chapters, cover_bytes?)` → write EPUB path.
4. Return `DownloadResult` with `epub_path`.

## EPUB contents

- Metadata: title, author, language `en`, identifier `royalroad-{fiction_id}`
- Optional cover image
- One XHTML chapter per downloaded chapter; TOC + nav spine
- Chapter body: `markdown` conversion of `markdown_body` (tables remain HTML)

## Non-goals

- CSS theming beyond minimal readability
- Multi-volume books
- Offline rebuild-from-md command (can add later)
