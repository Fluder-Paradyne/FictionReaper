"""Royal Road URL classification and normalization."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from fictionreaper.exceptions import InvalidURLError
from fictionreaper.models import ResolvedURL, UrlKind

_FICTION_RE: re.Pattern[str] = re.compile(
    r"^/fiction/(?P<fiction_id>\d+)/(?P<fiction_slug>[^/]+)/?$"
)
_CHAPTER_RE: re.Pattern[str] = re.compile(
    r"^/fiction/(?P<fiction_id>\d+)/(?P<fiction_slug>[^/]+)"
    r"/chapter/(?P<chapter_id>\d+)/(?P<chapter_slug>[^/]+)/?$"
)
_ALLOWED_HOSTS: frozenset[str] = frozenset({"royalroad.com", "www.royalroad.com"})


def resolve_url(url: str) -> ResolvedURL:
    """Classify and normalize a Royal Road fiction or chapter URL.

    Args:
        url: Absolute URL pointing at a fiction page or chapter page.

    Returns:
        A frozen :class:`ResolvedURL`.

    Raises:
        InvalidURLError: If the URL is not a supported Royal Road target.
    """
    raw: str = url.strip()
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        raise InvalidURLError(f"URL must be http(s): {url!r}")
    host: str = (parsed.hostname or "").lower()
    if host not in _ALLOWED_HOSTS:
        raise InvalidURLError(f"Not a Royal Road host: {host!r}")

    path: str = parsed.path.rstrip("/") or "/"
    # re-add nothing; matchers use optional trailing slash via $
    # Match with optional trailing slash by testing both forms
    path_for_match: str = path if path.startswith("/") else f"/{path}"

    chapter_match: re.Match[str] | None = _CHAPTER_RE.match(path_for_match)
    if chapter_match is not None:
        fiction_id: int = int(chapter_match.group("fiction_id"))
        fiction_slug: str = chapter_match.group("fiction_slug")
        chapter_id: int = int(chapter_match.group("chapter_id"))
        chapter_slug: str = chapter_match.group("chapter_slug")
        canonical: str = (
            f"https://www.royalroad.com/fiction/{fiction_id}/{fiction_slug}"
            f"/chapter/{chapter_id}/{chapter_slug}"
        )
        return ResolvedURL(
            kind=UrlKind.CHAPTER,
            fiction_id=fiction_id,
            fiction_slug=fiction_slug,
            chapter_id=chapter_id,
            chapter_slug=chapter_slug,
            canonical_url=canonical,
        )

    fiction_match: re.Match[str] | None = _FICTION_RE.match(path_for_match)
    if fiction_match is not None:
        fiction_id = int(fiction_match.group("fiction_id"))
        fiction_slug = fiction_match.group("fiction_slug")
        canonical = f"https://www.royalroad.com/fiction/{fiction_id}/{fiction_slug}"
        return ResolvedURL(
            kind=UrlKind.FICTION,
            fiction_id=fiction_id,
            fiction_slug=fiction_slug,
            chapter_id=None,
            chapter_slug=None,
            canonical_url=canonical,
        )

    raise InvalidURLError(f"Unsupported Royal Road URL path: {path_for_match!r}")


def fiction_url(fiction_id: int, fiction_slug: str) -> str:
    """Build a canonical fiction homepage URL."""
    return f"https://www.royalroad.com/fiction/{fiction_id}/{fiction_slug}"


def absolutize_rr_path(path: str) -> str:
    """Turn a site-relative path into an absolute www.royalroad.com URL."""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"https://www.royalroad.com{path}"
