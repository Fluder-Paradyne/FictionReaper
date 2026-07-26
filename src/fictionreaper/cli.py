"""Typer CLI for FictionReaper."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from fictionreaper import __version__
from fictionreaper.exceptions import FictionReaperError
from fictionreaper.models import DownloadRequest, DownloadResult, OutputFormat
from fictionreaper.pipeline import download

app: typer.Typer = typer.Typer(
    name="fictionreaper",
    help="Download Royal Road fiction chapters as Markdown and/or EPUB.",
    add_completion=False,
    no_args_is_help=True,
    invoke_without_command=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"fictionreaper {__version__}")
        raise typer.Exit()


def _parse_formats(values: list[str]) -> tuple[OutputFormat, ...]:
    """Parse repeated and/or comma-separated --format values."""
    parsed: list[OutputFormat] = []
    for value in values:
        for part in value.split(","):
            token: str = part.strip().lower()
            if not token:
                continue
            try:
                parsed.append(OutputFormat(token))
            except ValueError as exc:
                allowed: str = ", ".join(f.value for f in OutputFormat)
                raise typer.BadParameter(
                    f"Invalid format {token!r}. Choose from: {allowed}"
                ) from exc
    if not parsed:
        raise typer.BadParameter("At least one --format is required")
    # dedupe preserve order
    seen: set[OutputFormat] = set()
    unique: list[OutputFormat] = []
    for fmt in parsed:
        if fmt not in seen:
            seen.add(fmt)
            unique.append(fmt)
    return tuple(unique)


@app.callback()
def _root(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """FictionReaper — Royal Road → Markdown and/or EPUB."""
    _ = version


@app.command("download")
def download_cmd(
    url: Annotated[str, typer.Argument(help="Royal Road fiction or chapter URL")],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Base directory for downloads (default: ./downloads)",
        ),
    ] = Path("downloads"),
    delay: Annotated[
        float,
        typer.Option(
            "--delay",
            "-d",
            help="Seconds to wait between HTTP requests",
        ),
    ] = 1.0,
    format: Annotated[
        list[str] | None,
        typer.Option(
            "--format",
            "-f",
            help=(
                "Output format: markdown and/or epub. "
                "Repeat or comma-separate (default: markdown,epub)."
            ),
        ),
    ] = None,
) -> None:
    """Download chapters for a fiction homepage or a single chapter URL."""
    if delay < 0:
        typer.secho("Error: --delay must be >= 0", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    formats: tuple[OutputFormat, ...]
    if format is None:
        formats = (OutputFormat.MARKDOWN, OutputFormat.EPUB)
    else:
        formats = _parse_formats(format)

    request: DownloadRequest = DownloadRequest(
        url=url,  # type: ignore[arg-type]
        output_dir=output_dir,
        delay_seconds=delay,
        formats=formats,
    )
    try:
        result: DownloadResult = asyncio.run(download(request))
    except FictionReaperError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001
        typer.secho(f"Unexpected error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho(
        f"Downloaded {len(result.chapters)} chapter(s) "
        f"of {result.fiction_title!r} → {result.output_dir}",
        fg=typer.colors.GREEN,
    )
    for written in result.chapters:
        if written.path is not None:
            typer.echo(f"  {written.path}")
    if result.epub_path is not None:
        typer.echo(f"  EPUB: {result.epub_path}")


@app.command("serve")
def serve_cmd(
    host: Annotated[
        str,
        typer.Option("--host", help="Bind address"),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Bind port"),
    ] = 8000,
    reload: Annotated[
        bool,
        typer.Option("--reload", help="Reload on code changes (development)"),
    ] = False,
) -> None:
    """Run the FictionReaper HTTP API (FastAPI + uvicorn)."""
    import uvicorn

    typer.echo(f"Starting FictionReaper API on http://{host}:{port}")
    typer.echo(f"OpenAPI docs: http://{host}:{port}/docs")
    uvicorn.run(
        "fictionreaper.api:app",
        host=host,
        port=port,
        reload=reload,
    )


def run() -> None:
    """Console script entrypoint."""
    app()


if __name__ == "__main__":
    run()
