"""CLI smoke tests."""

from __future__ import annotations

from pathlib import Path

import httpx
import respx
from typer.testing import CliRunner

from fictionreaper.cli import app

runner = CliRunner()

FICTION_URL = "https://www.royalroad.com/fiction/21220/mother-of-learning"
CHAPTER_URL = (
    "https://www.royalroad.com/fiction/21220/mother-of-learning"
    "/chapter/301778/1-good-morning-brother"
)
CHAPTER2_URL = (
    "https://www.royalroad.com/fiction/21220/mother-of-learning"
    "/chapter/301781/2-lifes-little-problems"
)
CHAPTER3_URL = (
    "https://www.royalroad.com/fiction/21220/mother-of-learning"
    "/chapter/301784/3-the-bitter-truth"
)


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "fictionreaper" in result.stdout


def test_cli_download(
    fiction_html: str,
    tmp_path: Path,
) -> None:
    def ch_html(title: str, body: str) -> str:
        return f"""<!DOCTYPE html><html><body>
        <h1>{title}</h1>
        <div class="chapter-inner chapter-content"><p>{body}</p></div>
        </body></html>"""

    with respx.mock(assert_all_called=False) as router:
        router.get(FICTION_URL).mock(
            return_value=httpx.Response(200, text=fiction_html)
        )
        router.get(CHAPTER_URL).mock(
            return_value=httpx.Response(200, text=ch_html("C1", "A"))
        )
        router.get(CHAPTER2_URL).mock(
            return_value=httpx.Response(200, text=ch_html("C2", "B"))
        )
        router.get(CHAPTER3_URL).mock(
            return_value=httpx.Response(200, text=ch_html("C3", "C"))
        )
        result = runner.invoke(
            app,
            [
                "download",
                FICTION_URL,
                "--output-dir",
                str(tmp_path),
                "--delay",
                "0",
            ],
        )

    assert result.exit_code == 0, result.output
    assert "Downloaded 3" in result.output
