"""Async download orchestration."""

from __future__ import annotations

from pathlib import Path

from fictionreaper.exceptions import FetchError, ParseError
from fictionreaper.fetch import AsyncFetcher
from fictionreaper.models import (
    ChapterContent,
    ChapterRef,
    DownloadRequest,
    DownloadResult,
    FictionMeta,
    ResolvedURL,
    UrlKind,
    WrittenChapter,
)
from fictionreaper.parse import parse_chapter_page, parse_fiction_page
from fictionreaper.urls import fiction_url, resolve_url
from fictionreaper.write import safe_filename_component, write_chapter


async def download(request: DownloadRequest) -> DownloadResult:
    """Download chapter(s) for a fiction or chapter URL into Markdown files."""
    resolved: ResolvedURL = resolve_url(str(request.url))
    async with AsyncFetcher(
        user_agent=request.user_agent,
        delay_seconds=request.delay_seconds,
    ) as fetcher:
        if resolved.kind is UrlKind.FICTION:
            return await _download_fiction(resolved, request, fetcher)
        return await _download_single_chapter(resolved, request, fetcher)


async def _download_fiction(
    resolved: ResolvedURL,
    request: DownloadRequest,
    fetcher: AsyncFetcher,
) -> DownloadResult:
    html: str = await fetcher.get_text(resolved.canonical_url)
    meta: FictionMeta = parse_fiction_page(html, page_url=resolved.canonical_url)
    out_dir: Path = request.output_dir / safe_filename_component(meta.slug)
    written: list[WrittenChapter] = []
    for ref in meta.chapters:
        chapter_html: str = await fetcher.get_text(ref.url)
        chapter: ChapterContent = parse_chapter_page(chapter_html, page_url=ref.url)
        # Prefer fiction title/author from meta
        chapter = chapter.model_copy(
            update={
                "fiction_title": meta.title,
                "author": meta.author,
            }
        )
        written.append(write_chapter(chapter, output_dir=out_dir, index=ref.index))
    return DownloadResult(
        fiction_title=meta.title,
        fiction_slug=meta.slug,
        fiction_id=meta.fiction_id,
        output_dir=out_dir,
        chapters=written,
        kind=UrlKind.FICTION,
    )


async def _download_single_chapter(
    resolved: ResolvedURL,
    request: DownloadRequest,
    fetcher: AsyncFetcher,
) -> DownloadResult:
    assert resolved.chapter_id is not None
    assert resolved.chapter_slug is not None
    chapter_html: str = await fetcher.get_text(resolved.canonical_url)
    chapter: ChapterContent = parse_chapter_page(
        chapter_html, page_url=resolved.canonical_url
    )

    # Optionally enrich from fiction page for consistent title/author and index
    fic_page_url: str = fiction_url(resolved.fiction_id, resolved.fiction_slug)
    index: int = 1
    fiction_title: str = chapter.fiction_title
    author: str | None = chapter.author
    try:
        fic_html: str = await fetcher.get_text(fic_page_url)
        meta: FictionMeta = parse_fiction_page(fic_html, page_url=fic_page_url)
        fiction_title = meta.title
        author = meta.author
        matched_index: int | None = None
        for ref in meta.chapters:
            if ref.chapter_id == resolved.chapter_id:
                matched_index = ref.index
                break
        if matched_index is not None:
            index = matched_index
    except (FetchError, ParseError):
        # Still save the chapter if fiction page fails
        pass

    chapter = chapter.model_copy(
        update={
            "fiction_title": fiction_title,
            "author": author,
        }
    )
    out_dir: Path = request.output_dir / safe_filename_component(chapter.fiction_slug)
    written_one: WrittenChapter = write_chapter(chapter, output_dir=out_dir, index=index)
    return DownloadResult(
        fiction_title=fiction_title,
        fiction_slug=chapter.fiction_slug,
        fiction_id=chapter.fiction_id,
        output_dir=out_dir,
        chapters=[written_one],
        kind=UrlKind.CHAPTER,
    )


async def download_chapter_refs(
    refs: list[ChapterRef],
    *,
    fiction_title: str,
    fiction_slug: str,
    fiction_id: int,
    author: str,
    request: DownloadRequest,
    fetcher: AsyncFetcher,
) -> DownloadResult:
    """Download a pre-resolved list of chapter refs (testing / advanced use)."""
    out_dir: Path = request.output_dir / safe_filename_component(fiction_slug)
    written: list[WrittenChapter] = []
    for ref in refs:
        chapter_html: str = await fetcher.get_text(ref.url)
        chapter: ChapterContent = parse_chapter_page(chapter_html, page_url=ref.url)
        chapter = chapter.model_copy(
            update={"fiction_title": fiction_title, "author": author}
        )
        written.append(write_chapter(chapter, output_dir=out_dir, index=ref.index))
    return DownloadResult(
        fiction_title=fiction_title,
        fiction_slug=fiction_slug,
        fiction_id=fiction_id,
        output_dir=out_dir,
        chapters=written,
        kind=UrlKind.FICTION,
    )
