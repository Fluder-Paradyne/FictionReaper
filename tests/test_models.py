"""Tests for Pydantic models / formats."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from fictionreaper.models import DownloadRequest, OutputFormat


def test_default_formats() -> None:
    req = DownloadRequest(url="https://www.royalroad.com/fiction/1/x")  # type: ignore[arg-type]
    assert req.formats == (OutputFormat.MARKDOWN, OutputFormat.EPUB)
    assert req.wants_markdown()
    assert req.wants_epub()


def test_formats_from_comma_string() -> None:
    req = DownloadRequest(
        url="https://www.royalroad.com/fiction/1/x",  # type: ignore[arg-type]
        formats="markdown",  # type: ignore[arg-type]
    )
    assert req.formats == (OutputFormat.MARKDOWN,)
    assert not req.wants_epub()


def test_formats_dedupe() -> None:
    req = DownloadRequest(
        url="https://www.royalroad.com/fiction/1/x",  # type: ignore[arg-type]
        formats=(OutputFormat.EPUB, OutputFormat.EPUB, OutputFormat.MARKDOWN),
    )
    assert req.formats == (OutputFormat.EPUB, OutputFormat.MARKDOWN)


def test_formats_empty_rejected() -> None:
    with pytest.raises(ValidationError):
        DownloadRequest(
            url="https://www.royalroad.com/fiction/1/x",  # type: ignore[arg-type]
            formats=(),
        )
