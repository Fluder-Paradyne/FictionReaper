"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"


@pytest.fixture
def fiction_html() -> str:
    return (FIXTURES_DIR / "fiction_page.html").read_text(encoding="utf-8")


@pytest.fixture
def chapter_html() -> str:
    return (FIXTURES_DIR / "chapter_page.html").read_text(encoding="utf-8")


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR
