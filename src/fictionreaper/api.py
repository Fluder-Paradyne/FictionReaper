"""Small FastAPI server wrapping the download pipeline."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from fictionreaper import __version__
from fictionreaper.exceptions import FictionReaperError, InvalidURLError
from fictionreaper.models import DownloadRequest, DownloadResult, OutputFormat, UrlKind
from fictionreaper.pipeline import download

app: FastAPI = FastAPI(
    title="FictionReaper",
    description="Download Royal Road chapters as Markdown and/or EPUB.",
    version=__version__,
)


class DownloadBody(BaseModel):
    """JSON body for POST /download."""

    model_config = ConfigDict(frozen=True)

    url: HttpUrl
    output_dir: Path = Path("downloads")
    delay_seconds: float = Field(default=1.0, ge=0.0)
    formats: list[OutputFormat] = Field(
        default_factory=lambda: [OutputFormat.MARKDOWN, OutputFormat.EPUB],
        min_length=1,
        description="Output formats: markdown and/or epub",
    )


class WrittenChapterOut(BaseModel):
    """Serialized written chapter for API responses."""

    model_config = ConfigDict(frozen=True)

    title: str
    chapter_id: int
    path: str | None
    source_url: str


class DownloadResponse(BaseModel):
    """API response for a completed download."""

    model_config = ConfigDict(frozen=True)

    fiction_title: str
    fiction_slug: str
    fiction_id: int
    output_dir: str
    kind: UrlKind
    formats: list[OutputFormat]
    chapter_count: int
    chapters: list[WrittenChapterOut]
    epub_path: str | None = None


class HealthResponse(BaseModel):
    """Liveness payload."""

    model_config = ConfigDict(frozen=True)

    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health."""
    return HealthResponse(status="ok", version=__version__)


@app.post(
    "/download",
    response_model=DownloadResponse,
    status_code=status.HTTP_200_OK,
)
async def download_endpoint(body: DownloadBody) -> DownloadResponse:
    """Scrape the given Royal Road URL and write the requested formats to disk."""
    request: DownloadRequest = DownloadRequest(
        url=body.url,
        output_dir=body.output_dir,
        delay_seconds=body.delay_seconds,
        formats=tuple(body.formats),
    )
    try:
        result: DownloadResult = await download(request)
    except InvalidURLError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except FictionReaperError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    chapters_out: list[WrittenChapterOut] = [
        WrittenChapterOut(
            title=w.chapter.title,
            chapter_id=w.chapter.chapter_id,
            path=str(w.path) if w.path is not None else None,
            source_url=w.chapter.url,
        )
        for w in result.chapters
    ]
    return DownloadResponse(
        fiction_title=result.fiction_title,
        fiction_slug=result.fiction_slug,
        fiction_id=result.fiction_id,
        output_dir=str(result.output_dir),
        kind=result.kind,
        formats=list(result.formats),
        chapter_count=len(result.chapters),
        chapters=chapters_out,
        epub_path=str(result.epub_path) if result.epub_path is not None else None,
    )


def create_app() -> FastAPI:
    """Factory for tests and ASGI servers."""
    return app
