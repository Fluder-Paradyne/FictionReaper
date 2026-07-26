"""Pydantic models for Royal Road scraping and downloads."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class UrlKind(StrEnum):
    """Classification of a Royal Road URL."""

    FICTION = "fiction"
    CHAPTER = "chapter"


class OutputFormat(StrEnum):
    """Output formats a download can produce."""

    MARKDOWN = "markdown"
    EPUB = "epub"


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
    """A chapter produced by a download (path set when Markdown was written)."""

    model_config = ConfigDict(frozen=True)

    chapter: ChapterContent
    path: Path | None = None


class DownloadRequest(BaseModel):
    """Input for a download job (shared by CLI and API)."""

    model_config = ConfigDict(frozen=True)

    url: HttpUrl
    output_dir: Path = Path("downloads")
    delay_seconds: float = Field(default=1.0, ge=0.0)
    formats: tuple[OutputFormat, ...] = (OutputFormat.MARKDOWN, OutputFormat.EPUB)
    user_agent: str = "FictionReaper/0.1 (+https://github.com/Fluder-Paradyne/FictionReaper)"

    @field_validator("formats", mode="before")
    @classmethod
    def _coerce_formats(cls, value: object) -> tuple[OutputFormat, ...]:
        if value is None:
            return (OutputFormat.MARKDOWN, OutputFormat.EPUB)
        raw_items: list[object]
        if isinstance(value, str):
            raw_items = [p.strip() for p in value.split(",") if p.strip()]
        elif isinstance(value, (set, frozenset, list, tuple)):
            raw_items = list(value)
        else:
            raise TypeError("formats must be a string or sequence of format names")

        parsed: list[OutputFormat] = []
        for item in raw_items:
            if isinstance(item, OutputFormat):
                parsed.append(item)
            else:
                parsed.append(OutputFormat(str(item).strip().lower()))

        seen: set[OutputFormat] = set()
        unique: list[OutputFormat] = []
        for fmt in parsed:
            if fmt not in seen:
                seen.add(fmt)
                unique.append(fmt)
        if not unique:
            raise ValueError("formats must include at least one of: markdown, epub")
        return tuple(unique)

    def wants_markdown(self) -> bool:
        return OutputFormat.MARKDOWN in self.formats

    def wants_epub(self) -> bool:
        return OutputFormat.EPUB in self.formats


class DownloadResult(BaseModel):
    """Outcome of a download job."""

    model_config = ConfigDict(frozen=True)

    fiction_title: str
    fiction_slug: str
    fiction_id: int
    output_dir: Path
    chapters: list[WrittenChapter]
    kind: UrlKind
    formats: tuple[OutputFormat, ...]
    epub_path: Path | None = None
