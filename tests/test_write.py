"""Tests for Markdown writer."""

from __future__ import annotations

from pathlib import Path

from fictionreaper.models import ChapterContent
from fictionreaper.write import (
    chapter_filename,
    render_chapter_markdown,
    safe_filename_component,
    write_chapter,
)


def test_chapter_filename() -> None:
    assert chapter_filename(1, "hello-world") == "0001-hello-world.md"
    assert chapter_filename(42, "x") == "0042-x.md"


def test_safe_filename() -> None:
    assert "/" not in safe_filename_component('a/b:c*?"')


def test_write_chapter(tmp_path: Path) -> None:
    chapter = ChapterContent(
        fiction_id=1,
        fiction_title="Demo",
        fiction_slug="demo",
        chapter_id=99,
        title="Chapter One",
        slug="chapter-one",
        url="https://www.royalroad.com/fiction/1/demo/chapter/99/chapter-one",
        markdown_body="Hello **world**.\n",
    )
    written = write_chapter(chapter, output_dir=tmp_path / "demo", index=1)
    assert written.path.exists()
    text = written.path.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "Chapter One" in text
    assert "Hello **world**" in text
    assert render_chapter_markdown(chapter) == text
