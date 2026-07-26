"""Tests for EPUB builder."""

from __future__ import annotations

import zipfile
from pathlib import Path

from fictionreaper.epub import build_epub, epub_output_path, markdown_to_xhtml_fragment
from fictionreaper.models import ChapterContent


def _chapter(
    *,
    title: str = "Chapter One",
    slug: str = "chapter-one",
    body: str = "Hello **world**.\n",
    chapter_id: int = 1,
) -> ChapterContent:
    return ChapterContent(
        fiction_id=21220,
        fiction_title="Mother of Learning",
        fiction_slug="mother-of-learning",
        chapter_id=chapter_id,
        title=title,
        slug=slug,
        url=f"https://www.royalroad.com/fiction/21220/mother-of-learning/chapter/{chapter_id}/{slug}",
        markdown_body=body,
        author="nobody103",
    )


def test_markdown_to_xhtml_preserves_tables() -> None:
    md = "Intro\n\n<table><tr><td>A</td></tr></table>\n\nOutro\n"
    html = markdown_to_xhtml_fragment(md)
    assert "<table>" in html
    assert "<td>A</td>" in html
    bold_html = markdown_to_xhtml_fragment("**bold**")
    assert "bold" in bold_html
    assert "<strong>" in bold_html or "<b>" in bold_html


def test_epub_output_path() -> None:
    path = epub_output_path(Path("downloads/mother-of-learning"), "mother-of-learning")
    assert path == Path("downloads/mother-of-learning/mother-of-learning.epub")


def test_build_epub_with_cover(tmp_path: Path) -> None:
    cover = (Path(__file__).parent / "fixtures" / "cover.png").read_bytes()
    out = tmp_path / "book.epub"
    chapters = [
        _chapter(title="C1", slug="c1", body="First.\n", chapter_id=1),
        _chapter(
            title="C2",
            slug="c2",
            body="Second with table.\n\n<table><tr><td>X</td></tr></table>\n",
            chapter_id=2,
        ),
    ]
    path = build_epub(
        fiction_id=21220,
        fiction_title="Mother of Learning",
        fiction_slug="mother-of-learning",
        author="nobody103",
        chapters=chapters,
        output_path=out,
        cover_bytes=cover,
        cover_url="https://example.com/cover.png",
    )
    assert path == out
    assert out.exists()
    assert out.stat().st_size > 100

    with zipfile.ZipFile(out, "r") as zf:
        names = set(zf.namelist())
        assert "mimetype" in names
        assert any(n.endswith(".xhtml") or n.endswith(".html") for n in names)
        # cover present
        assert any("cover" in n.lower() for n in names)
        # content includes chapter text
        xhtml_files = [n for n in names if n.endswith(".xhtml") or n.endswith(".html")]
        joined = b""
        for name in xhtml_files:
            joined += zf.read(name)
        assert b"First." in joined or b"First" in joined
        assert b"<table>" in joined or b"table" in joined.lower()


def test_build_epub_without_cover(tmp_path: Path) -> None:
    out = tmp_path / "plain.epub"
    build_epub(
        fiction_id=1,
        fiction_title="Demo",
        fiction_slug="demo",
        author="A",
        chapters=[_chapter()],
        output_path=out,
        cover_bytes=None,
    )
    assert out.exists()
    with zipfile.ZipFile(out, "r") as zf:
        assert "mimetype" in zf.namelist()
