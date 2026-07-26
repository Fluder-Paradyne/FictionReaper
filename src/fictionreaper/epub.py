"""Build EPUB books from downloaded chapter content."""

from __future__ import annotations

import re
from pathlib import Path

import markdown
from ebooklib import epub

from fictionreaper.models import ChapterContent
from fictionreaper.write import safe_filename_component

_MD: markdown.Markdown = markdown.Markdown(
    extensions=["extra", "sane_lists", "smarty"],
    output_format="xhtml",
)

_DEFAULT_CSS: str = """
body {
  font-family: serif;
  line-height: 1.5;
  margin: 1em;
}
h1 { font-size: 1.4em; margin-bottom: 1em; }
table {
  border-collapse: collapse;
  margin: 1em 0;
  width: 100%;
}
th, td {
  border: 1px solid #888;
  padding: 0.35em 0.5em;
  vertical-align: top;
}
img.cover { max-width: 100%; height: auto; }
"""


def markdown_to_xhtml_fragment(md_text: str) -> str:
    """Convert chapter Markdown (including raw HTML tables) to an XHTML fragment."""
    _MD.reset()
    html: str = _MD.convert(md_text)
    return html


def _escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _cover_extension(cover_bytes: bytes, cover_url: str | None) -> str:
    """Guess image file extension for the cover."""
    if cover_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if cover_bytes[:2] == b"\xff\xd8":
        return "jpg"
    if cover_bytes[:6] in {b"GIF87a", b"GIF89a"}:
        return "gif"
    if cover_bytes[:4] == b"RIFF" and cover_bytes[8:12] == b"WEBP":
        return "webp"
    if cover_url:
        lower: str = cover_url.lower().split("?", 1)[0]
        for ext in ("png", "jpg", "jpeg", "gif", "webp"):
            if lower.endswith(f".{ext}"):
                return "jpg" if ext == "jpeg" else ext
    return "jpg"


def _chapter_file_name(index: int, slug: str) -> str:
    safe: str = re.sub(r"[^a-zA-Z0-9._-]+", "-", slug).strip("-") or "chapter"
    return f"chap_{index:04d}_{safe}.xhtml"


def build_epub(
    *,
    fiction_id: int,
    fiction_title: str,
    fiction_slug: str,
    author: str,
    chapters: list[ChapterContent],
    output_path: Path,
    cover_bytes: bytes | None = None,
    cover_url: str | None = None,
    language: str = "en",
) -> Path:
    """Write an EPUB containing ``chapters`` to ``output_path``.

    Returns:
        The path written (same as ``output_path``).
    """
    if not chapters:
        raise ValueError("Cannot build EPUB with zero chapters")

    book: epub.EpubBook = epub.EpubBook()
    book.set_identifier(f"royalroad-{fiction_id}")
    book.set_title(fiction_title)
    book.set_language(language)
    book.add_author(author or "Unknown")
    book.add_metadata("DC", "source", f"https://www.royalroad.com/fiction/{fiction_id}/{fiction_slug}")

    style: epub.EpubItem = epub.EpubItem(
        uid="style_default",
        file_name="style/default.css",
        media_type="text/css",
        content=_DEFAULT_CSS.encode("utf-8"),
    )
    book.add_item(style)

    if cover_bytes:
        ext: str = _cover_extension(cover_bytes, cover_url)
        book.set_cover(f"cover.{ext}", cover_bytes)

    epub_chapters: list[epub.EpubHtml] = []
    for index, chapter in enumerate(chapters, start=1):
        file_name: str = _chapter_file_name(index, chapter.slug)
        body_html: str = markdown_to_xhtml_fragment(chapter.markdown_body)
        title_xml: str = _escape_xml(chapter.title)
        # ebooklib expects a body fragment (it wraps document structure itself).
        content: str = f"<h1>{title_xml}</h1>\n{body_html}"
        item: epub.EpubHtml = epub.EpubHtml(
            title=chapter.title,
            file_name=file_name,
            lang=language,
        )
        item.set_content(content.encode("utf-8"))
        item.add_item(style)
        book.add_item(item)
        epub_chapters.append(item)

    book.toc = tuple(epub_chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", *epub_chapters]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), book, {})
    return output_path


def epub_output_path(output_dir: Path, fiction_slug: str) -> Path:
    """Default EPUB path next to chapter Markdown files."""
    safe_slug: str = safe_filename_component(fiction_slug)
    return output_dir / f"{safe_slug}.epub"
