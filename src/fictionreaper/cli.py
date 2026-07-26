"""Typer CLI for FictionReaper."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from fictionreaper import __version__
from fictionreaper.exceptions import FictionReaperError
from fictionreaper.models import DownloadRequest, DownloadResult
from fictionreaper.pipeline import download

app: typer.Typer = typer.Typer(
    name="fictionreaper",
    help="Download Royal Road fiction chapters as Markdown and EPUB.",
    add_completion=False,
    no_args_is_help=True,
    invoke_without_command=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"fictionreaper {__version__}")
        raise typer.Exit()


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
    """FictionReaper — Royal Road → Markdown + EPUB."""
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
    no_epub: Annotated[
        bool,
        typer.Option(
            "--no-epub",
            help="Skip writing an EPUB (Markdown only)",
        ),
    ] = False,
) -> None:
    """Download chapters for a fiction homepage or a single chapter URL."""
    if delay < 0:
        typer.secho("Error: --delay must be >= 0", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    request: DownloadRequest = DownloadRequest(
        url=url,  # type: ignore[arg-type]
        output_dir=output_dir,
        delay_seconds=delay,
        write_epub=not no_epub,
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
        typer.echo(f"  {written.path}")
    if result.epub_path is not None:
        typer.echo(f"  EPUB: {result.epub_path}")


def run() -> None:
    """Console script entrypoint."""
    app()


if __name__ == "__main__":
    run()
