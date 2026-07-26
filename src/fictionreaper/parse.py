"""HTML parsers for Royal Road fiction and chapter pages."""

from __future__ import annotations

import re
from html import unescape

from bs4 import BeautifulSoup, NavigableString, Tag

from fictionreaper.exceptions import ParseError
from fictionreaper.models import ChapterContent, ChapterRef, FictionMeta
from fictionreaper.urls import absolutize_rr_path, fiction_url

_CHAPTER_PATH_RE: re.Pattern[str] = re.compile(
    r"/fiction/(?P<fiction_id>\d+)/(?P<fiction_slug>[^/]+)"
    r"/chapter/(?P<chapter_id>\d+)/(?P<chapter_slug>[^/]+)"
)
_FICTION_PATH_RE: re.Pattern[str] = re.compile(
    r"/fiction/(?P<fiction_id>\d+)/(?P<fiction_slug>[^/]+)/?$"
)
_SLUG_SAFE_RE: re.Pattern[str] = re.compile(r"[^a-z0-9]+")


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _text(el: Tag | NavigableString | None) -> str:
    if el is None:
        return ""
    value: str = el.get_text(" ", strip=True)
    return unescape(value)


def slugify(value: str) -> str:
    """Create a filesystem-friendly slug from a title."""
    lowered: str = value.strip().lower()
    slug: str = _SLUG_SAFE_RE.sub("-", lowered).strip("-")
    return slug or "chapter"


def parse_fiction_page(html: str, *, page_url: str) -> FictionMeta:
    """Parse a fiction homepage into metadata and chapter TOC."""
    soup: BeautifulSoup = _soup(html)

    fiction_id: int | None = None
    fiction_slug: str | None = None
    path_match: re.Match[str] | None = _FICTION_PATH_RE.search(
        page_url.replace("https://www.royalroad.com", "").replace(
            "http://www.royalroad.com", ""
        )
    )
    if path_match is None:
        # tolerate non-www or trailing pieces
        path_match = re.search(
            r"/fiction/(?P<fiction_id>\d+)/(?P<fiction_slug>[^/?#]+)", page_url
        )
    if path_match is not None:
        fiction_id = int(path_match.group("fiction_id"))
        fiction_slug = path_match.group("fiction_slug")

    title: str = ""
    h1: Tag | None = soup.select_one("h1")
    if h1 is not None:
        title = _text(h1)
    if not title:
        og: Tag | None = soup.select_one('meta[property="og:title"]')
        if og is not None and og.get("content"):
            title = str(og["content"]).split("|")[0].strip()
    if not title:
        raise ParseError("Could not find fiction title")

    author: str = "Unknown"
    author_link: Tag | None = soup.select_one("h4 a[href*='/profile/']")
    if author_link is None:
        author_link = soup.select_one("a[href*='/profile/']")
    if author_link is not None:
        author = _text(author_link) or author

    chapters: list[ChapterRef] = []
    rows: list[Tag] = list(soup.select("tr.chapter-row"))
    if not rows:
        # fallback: chapter links in #chapters
        rows = []
    for index, row in enumerate(rows, start=1):
        data_url: str | list[str] | None = row.get("data-url")
        href: str
        if isinstance(data_url, str) and data_url:
            href = data_url
        else:
            link: Tag | None = row.select_one("a[href*='/chapter/']")
            if link is None or not link.get("href"):
                continue
            href = str(link["href"])
        abs_url: str = absolutize_rr_path(href)
        cm: re.Match[str] | None = _CHAPTER_PATH_RE.search(abs_url)
        if cm is None:
            continue
        link_el: Tag | None = row.select_one("a[href*='/chapter/']")
        ch_title: str = _text(link_el) if link_el is not None else cm.group("chapter_slug")
        chapters.append(
            ChapterRef(
                index=index,
                chapter_id=int(cm.group("chapter_id")),
                title=ch_title,
                slug=cm.group("chapter_slug"),
                url=abs_url,
            )
        )
        if fiction_id is None:
            fiction_id = int(cm.group("fiction_id"))
            fiction_slug = cm.group("fiction_slug")

    if fiction_id is None or fiction_slug is None:
        raise ParseError("Could not determine fiction id/slug from page")
    if not chapters:
        raise ParseError("No chapters found on fiction page")

    meta: FictionMeta = FictionMeta(
        fiction_id=fiction_id,
        title=title,
        slug=fiction_slug,
        author=author,
        url=fiction_url(fiction_id, fiction_slug),
        chapters=chapters,
    )
    return meta


# Structural table tags we keep when embedding HTML tables in Markdown.
_TABLE_TAGS: frozenset[str] = frozenset(
    {
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "th",
        "td",
        "caption",
        "colgroup",
        "col",
    }
)
# Attributes safe/useful to keep on table elements (layout + accessibility).
_TABLE_ATTRS: frozenset[str] = frozenset(
    {
        "colspan",
        "rowspan",
        "scope",
        "headers",
        "align",
        "valign",
        "span",  # col / colgroup
    }
)
# Inline tags allowed inside table cells when serializing HTML tables.
_TABLE_INLINE_TAGS: frozenset[str] = frozenset(
    {
        "strong",
        "b",
        "em",
        "i",
        "a",
        "br",
        "span",
        "sub",
        "sup",
        "u",
        "s",
        "code",
    }
)


def _escape_html_text(value: str) -> str:
    """Escape text for embedding inside preserved HTML tables."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _attr_string(node: Tag, allowed: frozenset[str]) -> str:
    """Build a space-prefixed attribute string from allowed attrs on ``node``."""
    attrs: list[str] = []
    for attr in allowed:
        if not node.has_attr(attr):
            continue
        raw: str | list[str] = node.get(attr)  # type: ignore[assignment]
        value: str = " ".join(raw) if isinstance(raw, list) else str(raw)
        safe: str = _escape_html_text(value).replace('"', "&quot;")
        attrs.append(f'{attr}="{safe}"')
    if not attrs:
        return ""
    return " " + " ".join(attrs)


def _serialize_table_cell_children(node: Tag) -> str:
    """Serialize allowed inline markup inside a table cell."""
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, NavigableString):
            parts.append(_escape_html_text(str(child)))
            continue
        if not isinstance(child, Tag):
            continue
        name: str | None = child.name
        if name in {"script", "style", "noscript"}:
            continue
        if name == "br":
            parts.append("<br/>")
            continue
        if name == "a":
            href_val: str | list[str] = child.get("href") or ""
            href_s: str = href_val if isinstance(href_val, str) else ""
            inner: str = _serialize_table_cell_children(child)
            if href_s:
                safe_href: str = _escape_html_text(href_s).replace('"', "&quot;")
                parts.append(f'<a href="{safe_href}">{inner}</a>')
            else:
                parts.append(inner)
            continue
        if name in _TABLE_INLINE_TAGS:
            # Normalize presentational tags to semantic ones where useful.
            tag_name: str = name
            if name == "b":
                tag_name = "strong"
            elif name == "i":
                tag_name = "em"
            inner = _serialize_table_cell_children(child)
            if tag_name == "span":
                # Drop class-only spans from RR; keep text content.
                parts.append(inner)
            else:
                parts.append(f"<{tag_name}>{inner}</{tag_name}>")
            continue
        # Unknown tags: keep their text/inline descendants only.
        parts.append(_serialize_table_cell_children(child))
    return "".join(parts)


def _serialize_table_node(node: Tag) -> str:
    """Serialize a table (or table subtree) to cleaned HTML."""
    name: str | None = node.name
    if name is None:
        return ""
    if name in {"script", "style", "noscript"}:
        return ""

    if name in {"th", "td"}:
        attr_str: str = _attr_string(node, _TABLE_ATTRS)
        inner: str = _serialize_table_cell_children(node).strip()
        return f"<{name}{attr_str}>{inner}</{name}>"

    if name in _TABLE_TAGS:
        attr_str = _attr_string(node, _TABLE_ATTRS)
        if name == "col":
            return f"<{name}{attr_str}/>"
        children_html: list[str] = []
        for child in node.children:
            if isinstance(child, Tag):
                piece: str = _serialize_table_node(child)
                if piece:
                    children_html.append(piece)
            elif isinstance(child, NavigableString) and name == "caption":
                text: str = str(child).strip()
                if text:
                    children_html.append(_escape_html_text(text))
        inner_joined: str = "".join(children_html)
        return f"<{name}{attr_str}>{inner_joined}</{name}>"

    # Non-table wrapper inside table (e.g. accidental div): flatten children
    pieces: list[str] = []
    for child in node.children:
        if isinstance(child, Tag):
            piece = _serialize_table_node(child)
            if piece:
                pieces.append(piece)
    return "".join(pieces)


def table_to_html(table: Tag) -> str:
    """Return a cleaned HTML ``<table>...</table>`` suitable for Markdown embeds."""
    if table.name != "table":
        raise ValueError(f"Expected <table>, got <{table.name}>")
    html: str = _serialize_table_node(table)
    # Pretty-ish: put each major row on its own line for readability
    html = re.sub(r"></(tr|thead|tbody|tfoot|table)>", r">\n</\1>", html)
    html = re.sub(r"<(tr|thead|tbody|tfoot)([ >])", r"\n<\1\2", html)
    html = re.sub(r"\n{2,}", "\n", html).strip()
    return html + "\n"


def _html_to_markdown(container: Tag) -> str:
    """Convert chapter HTML into Markdown, preserving HTML tables as HTML blocks."""
    lines: list[str] = []

    def walk(node: Tag | NavigableString) -> None:
        if isinstance(node, NavigableString):
            return
        name: str | None = node.name
        if name in {"script", "style", "noscript"}:
            return
        if name == "table":
            table_html: str = table_to_html(node).rstrip()
            if table_html:
                lines.append(table_html)
                lines.append("")
            return
        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level: int = int(name[1])
            text: str = _text(node)
            if text:
                lines.append(f"{'#' * level} {text}")
                lines.append("")
            return
        if name == "p":
            text = _inline_markdown(node)
            if text.strip():
                lines.append(text.strip())
                lines.append("")
            return
        if name in {"br"}:
            lines.append("")
            return
        if name in {"hr"}:
            lines.append("---")
            lines.append("")
            return
        if name in {"ul", "ol"}:
            items: list[Tag] = [c for c in node.children if isinstance(c, Tag) and c.name == "li"]
            for i, li in enumerate(items, start=1):
                prefix: str = f"{i}." if name == "ol" else "-"
                lines.append(f"{prefix} {_inline_markdown(li).strip()}")
            lines.append("")
            return
        if name == "blockquote":
            quoted: str = _inline_markdown(node).strip()
            for qline in quoted.splitlines() or [""]:
                lines.append(f"> {qline}")
            lines.append("")
            return
        for child in node.children:
            if isinstance(child, (Tag, NavigableString)):
                walk(child)

    walk(container)
    # collapse excessive blank lines
    cleaned: list[str] = []
    blank: bool = False
    for line in lines:
        if line.strip() == "":
            if not blank:
                cleaned.append("")
            blank = True
        else:
            cleaned.append(line)
            blank = False
    return "\n".join(cleaned).strip() + "\n"


def _emphasis_from_tag(node: Tag, marker: str) -> list[str]:
    """Convert a ``strong``/``em`` tag to Markdown pieces.

    Royal Road often writes titles as
    ``<strong>Chapter 001<br></strong><strong>Title</strong>``.
    We close emphasis before each ``<br>`` and emit a real newline so markers
    never glue into ``****`` (which CommonMark will not render as bold).
    """
    pieces: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        segment: str = "".join(buffer).strip()
        buffer.clear()
        if segment:
            pieces.append(f"{marker}{segment}{marker}")

    for child in node.children:
        if isinstance(child, NavigableString):
            buffer.append(str(child))
            continue
        if not isinstance(child, Tag):
            continue
        if child.name == "br":
            flush()
            pieces.append("\n")
            continue
        # Nested markup inside emphasis (e.g. strong > a, em > strong).
        nested: str = _inline_markdown(child)
        buffer.append(nested)
    flush()
    return pieces


def _inline_markdown(node: Tag) -> str:
    parts: list[str] = []

    def walk_inline(n: Tag | NavigableString) -> None:
        if isinstance(n, NavigableString):
            parts.append(str(n))
            return
        name: str | None = n.name
        if name in {"script", "style"}:
            return
        if name in {"strong", "b"}:
            parts.extend(_emphasis_from_tag(n, "**"))
            return
        if name in {"em", "i"}:
            parts.extend(_emphasis_from_tag(n, "*"))
            return
        if name == "br":
            parts.append("\n")
            return
        if name == "a":
            label: str = _text(n)
            href: str | list[str] = n.get("href") or ""
            href_s: str = href if isinstance(href, str) else ""
            if href_s:
                parts.append(f"[{label}]({href_s})")
            else:
                parts.append(label)
            return
        for child in n.children:
            if isinstance(child, (Tag, NavigableString)):
                walk_inline(child)

    walk_inline(node)
    text: str = "".join(parts)
    # Collapse horizontal whitespace but keep hard line breaks from <br>.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    # Safety net: adjacent emphasis without a break still must not glue.
    text = re.sub(r"\*\*\*\*", "** **", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(?=\*(?!\*))", "* ", text)
    return text.strip()


def parse_chapter_page(html: str, *, page_url: str) -> ChapterContent:
    """Parse a chapter page into title + Markdown body."""
    soup: BeautifulSoup = _soup(html)

    cm: re.Match[str] | None = _CHAPTER_PATH_RE.search(page_url)
    if cm is None:
        # try og:url
        og_url: Tag | None = soup.select_one('meta[property="og:url"]')
        if og_url is not None and og_url.get("content"):
            cm = _CHAPTER_PATH_RE.search(str(og_url["content"]))
    if cm is None:
        raise ParseError(f"Could not parse chapter ids from URL: {page_url}")

    fiction_id: int = int(cm.group("fiction_id"))
    fiction_slug: str = cm.group("fiction_slug")
    chapter_id: int = int(cm.group("chapter_id"))
    chapter_slug: str = cm.group("chapter_slug")

    title: str = ""
    h1: Tag | None = soup.select_one("h1")
    if h1 is not None:
        title = _text(h1)
    if not title:
        og_title: Tag | None = soup.select_one('meta[property="og:title"]')
        if og_title is not None and og_title.get("content"):
            raw_title: str = str(og_title["content"])
            title = raw_title.split(" - ")[0].strip() if " - " in raw_title else raw_title

    fiction_title: str = fiction_slug.replace("-", " ").title()
    # Prefer fic-header link that is not the chapter itself
    for candidate in soup.select("a[href*='/fiction/']"):
        href_val: str | list[str] = candidate.get("href") or ""
        href_s: str = href_val if isinstance(href_val, str) else ""
        if "/chapter/" in href_s:
            continue
        if _FICTION_PATH_RE.search(href_s) or re.search(
            rf"/fiction/{fiction_id}/{re.escape(fiction_slug)}", href_s
        ):
            t: str = _text(candidate)
            if t:
                fiction_title = t
                break

    content: Tag | None = soup.select_one("div.chapter-inner.chapter-content")
    if content is None:
        content = soup.select_one("div.chapter-content")
    if content is None:
        raise ParseError("Could not find chapter content container")

    markdown_body: str = _html_to_markdown(content)
    if not markdown_body.strip():
        raise ParseError("Chapter content was empty after conversion")

    return ChapterContent(
        fiction_id=fiction_id,
        fiction_title=fiction_title,
        fiction_slug=fiction_slug,
        chapter_id=chapter_id,
        title=title or chapter_slug,
        slug=chapter_slug,
        url=page_url if page_url.startswith("http") else absolutize_rr_path(page_url),
        markdown_body=markdown_body,
        author=None,
    )
