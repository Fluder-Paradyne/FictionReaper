"""Tests for URL resolution."""

from __future__ import annotations

import pytest

from fictionreaper.exceptions import InvalidURLError
from fictionreaper.models import UrlKind
from fictionreaper.urls import absolutize_rr_path, fiction_url, resolve_url


def test_resolve_fiction_url() -> None:
    resolved = resolve_url("https://www.royalroad.com/fiction/21220/mother-of-learning")
    assert resolved.kind is UrlKind.FICTION
    assert resolved.fiction_id == 21220
    assert resolved.fiction_slug == "mother-of-learning"
    assert resolved.chapter_id is None
    assert (
        resolved.canonical_url
        == "https://www.royalroad.com/fiction/21220/mother-of-learning"
    )


def test_resolve_chapter_url() -> None:
    url = (
        "https://www.royalroad.com/fiction/21220/mother-of-learning"
        "/chapter/301778/1-good-morning-brother"
    )
    resolved = resolve_url(url)
    assert resolved.kind is UrlKind.CHAPTER
    assert resolved.fiction_id == 21220
    assert resolved.chapter_id == 301778
    assert resolved.chapter_slug == "1-good-morning-brother"


def test_resolve_strips_trailing_slash() -> None:
    resolved = resolve_url("https://royalroad.com/fiction/1/foo/")
    assert resolved.fiction_id == 1
    assert resolved.fiction_slug == "foo"


def test_reject_non_rr_host() -> None:
    with pytest.raises(InvalidURLError, match="Not a Royal Road host"):
        resolve_url("https://example.com/fiction/1/foo")


def test_reject_unsupported_path() -> None:
    with pytest.raises(InvalidURLError, match="Unsupported"):
        resolve_url("https://www.royalroad.com/home")


def test_reject_bad_scheme() -> None:
    with pytest.raises(InvalidURLError, match="http"):
        resolve_url("ftp://www.royalroad.com/fiction/1/foo")


def test_fiction_url_helper() -> None:
    assert fiction_url(1, "x") == "https://www.royalroad.com/fiction/1/x"


def test_absolutize() -> None:
    assert absolutize_rr_path("/fiction/1/x") == "https://www.royalroad.com/fiction/1/x"
    assert (
        absolutize_rr_path("https://www.royalroad.com/fiction/1/x")
        == "https://www.royalroad.com/fiction/1/x"
    )
