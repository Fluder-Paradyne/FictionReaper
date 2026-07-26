"""Tests for HTML parsers."""

from __future__ import annotations

import re

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
    assert meta.cover_url is not None
    assert "mother-of-learning" in meta.cover_url or meta.cover_url.startswith("http")


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


def test_adjacent_strong_with_br_renders_as_separate_bold() -> None:
    """RR title lines often use <strong>…<br></strong><strong>…</strong>."""
    page_url = "https://www.royalroad.com/fiction/1/demo/chapter/2/title-line"
    html = """<!DOCTYPE html>
<html><body>
<h1>Title Line</h1>
<a href="/fiction/1/demo">Demo</a>
<div class="chapter-inner chapter-content">
<p style="text-align: center">
<strong>Chapter 001<br></strong><strong>Good Morning Brother</strong>
</p>
<p>Body text with <em>emphasis</em> here.</p>
</div>
</body></html>
"""
    chapter = parse_chapter_page(html, page_url=page_url)
    body = chapter.markdown_body
    # Must not glue into **** (breaks bold rendering in CommonMark)
    assert "****" not in body
    assert "**Chapter 001**" in body
    assert "**Good Morning Brother**" in body
    # Prefer a line break between the two bold runs (from <br>)
    assert re.search(
        r"\*\*Chapter 001\*\*\s*\n\s*\*\*Good Morning Brother\*\*",
        body,
    )


def test_html_tables_preserved_in_markdown() -> None:
    """HTML tables should appear as HTML blocks inside the Markdown body."""
    page_url = (
        "https://www.royalroad.com/fiction/1/demo/chapter/2/with-table"
    )
    html = """<!DOCTYPE html>
<html><body>
<h1>With Table</h1>
<a href="/fiction/1/demo">Demo Story</a>
<div class="chapter-inner chapter-content">
<p>Intro paragraph.</p>
<table class="rr-junk cnMabcdef" style="width:100%">
  <thead>
    <tr>
      <th class="noise">Stat</th>
      <th>Value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Strength</strong></td>
      <td colspan="1">10</td>
    </tr>
    <tr>
      <td>Agility</td>
      <td>12</td>
    </tr>
  </tbody>
</table>
<p>After the table.</p>
</div>
</body></html>
"""
    chapter = parse_chapter_page(html, page_url=page_url)
    body = chapter.markdown_body
    assert "Intro paragraph." in body
    assert "After the table." in body
    assert "<table>" in body
    assert "</table>" in body
    assert "<th>Stat</th>" in body
    assert "<th>Value</th>" in body
    assert "<td><strong>Strength</strong></td>" in body or "<td>**Strength**</td>" in body
    assert 'colspan="1"' in body or "10" in body
    # RR noise classes stripped from the preserved table
    assert "rr-junk" not in body
    assert "cnMabcdef" not in body
