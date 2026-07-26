"""Tests for HTML parsers."""

from __future__ import annotations

from fictionreaper.parse import parse_chapter_page, parse_fiction_page, slugify


def test_slugify() -> None:
    assert slugify("Good Morning Brother!") == "good-morning-brother"
    assert slugify("  ") == "chapter"


def test_parse_fiction_page(fiction_html: str) -> None:
    page_url = "https://www.royalroad.com/fiction/21220/mother-of-learning"
    meta = parse_fiction_page(fiction_html, page_url=page_url)
    assert meta.fiction_id == 21220
    assert meta.slug == "mother-of-learning"
    assert meta.title == "Mother of Learning"
    assert meta.author == "nobody103"
    assert len(meta.chapters) == 3
    first = meta.chapters[0]
    assert first.index == 1
    assert first.chapter_id == 301778
    assert "Good Morning" in first.title
    assert first.url.startswith("https://www.royalroad.com/")


def test_parse_chapter_page(chapter_html: str) -> None:
    page_url = (
        "https://www.royalroad.com/fiction/21220/mother-of-learning"
        "/chapter/301778/1-good-morning-brother"
    )
    chapter = parse_chapter_page(chapter_html, page_url=page_url)
    assert chapter.fiction_id == 21220
    assert chapter.chapter_id == 301778
    assert "Good Morning" in chapter.title
    assert "Zorian" in chapter.markdown_body or "eyes" in chapter.markdown_body.lower()
    assert chapter.markdown_body.endswith("\n")
