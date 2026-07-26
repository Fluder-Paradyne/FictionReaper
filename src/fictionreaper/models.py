"""Pydantic models for Royal Road scraping and downloads."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class UrlKind(StrEnum):
    """Classification of a Royal Road URL."""

    FICTION = "fiction"
    CHAPTER = "chapter"


class ResolvedURL(BaseModel):
    """A normalized, classified Royal Road URL."""

    model_config = ConfigDict(frozen=True)

    kind: UrlKind
    fiction_id: int = Field(ge=1)
    fiction_slug: str = Field(min_length=1)
    chapter_id: int | None = Field(default=None, ge=1)
    chapter_slug: str | None = None
    canonical_url: str


class ChapterRef(BaseModel):
    """A chapter entry from a fiction table of contents."""

    model_config = ConfigDict(frozen=True)

    index: int = Field(ge=1, description="1-based order in the TOC")
    chapter_id: int = Field(ge=1)
    title: str
    slug: str
    url: str


class FictionMeta(BaseModel):
    """Metadata for a Royal Road fiction."""

    model_config = ConfigDict(frozen=True)

    fiction_id: int = Field(ge=1)
    title: str
    slug: str
    author: str
    url: str
    chapters: list[ChapterRef]
    cover_url: str | None = None


class ChapterContent(BaseModel):
    """Parsed chapter page content."""

    model_config = ConfigDict(frozen=True)

    fiction_id: int = Field(ge=1)
    fiction_title: str
    fiction_slug: str
    chapter_id: int = Field(ge=1)
    title: str
    slug: str
    url: str
    markdown_body: str
    author: str | None = None


class WrittenChapter(BaseModel):
    """A chapter written to disk."""

    model_config = ConfigDict(frozen=True)

    chapter: ChapterContent
    path: Path


class DownloadRequest(BaseModel):
    """Input for a download job (shared by CLI and API)."""

    model_config = ConfigDict(frozen=True)

    url: HttpUrl
    output_dir: Path = Path("downloads")
    delay_seconds: float = Field(default=1.0, ge=0.0)
    write_epub: bool = True
    user_agent: str = "FictionReaper/0.1 (+https://github.com/Fluder-Paradyne/FictionReaper)"


class DownloadResult(BaseModel):
    """Outcome of a download job."""

    model_config = ConfigDict(frozen=True)

    fiction_title: str
    fiction_slug: str
    fiction_id: int
    output_dir: Path
    chapters: list[WrittenChapter]
    kind: UrlKind
    epub_path: Path | None = None
