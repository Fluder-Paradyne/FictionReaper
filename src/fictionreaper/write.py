"""Write chapter Markdown files to disk."""

from __future__ import annotations

import re
from pathlib import Path

from fictionreaper.models import ChapterContent, WrittenChapter

_UNSAFE_RE: re.Pattern[str] = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_filename_component(value: str) -> str:
    """Remove characters that are unsafe in file names."""
    cleaned: str = _UNSAFE_RE.sub("", value).strip().strip(".")
    return cleaned or "untitled"


def chapter_filename(index: int, slug: str) -> str:
    """Build ``NNNN-slug.md`` file name."""
    safe_slug: str = safe_filename_component(slug)
    return f"{index:04d}-{safe_slug}.md"


def render_chapter_markdown(chapter: ChapterContent) -> str:
    """Render a full Markdown document for a chapter."""
    lines: list[str] = [
        "---",
        f'title: "{_yaml_escape(chapter.title)}"',
        f'fiction: "{_yaml_escape(chapter.fiction_title)}"',
        f"source: {chapter.url}",
        f"chapter_id: {chapter.chapter_id}",
        f"fiction_id: {chapter.fiction_id}",
        "---",
        "",
        f"# {chapter.title}",
        "",
        chapter.markdown_body.rstrip(),
        "",
    ]
    return "\n".join(lines)


def _yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def write_chapter(
    chapter: ChapterContent,
    *,
    output_dir: Path,
    index: int,
) -> WrittenChapter:
    """Write one chapter Markdown file under ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename: str = chapter_filename(index, chapter.slug)
    path: Path = output_dir / filename
    content: str = render_chapter_markdown(chapter)
    path.write_text(content, encoding="utf-8")
    return WrittenChapter(chapter=chapter, path=path)
