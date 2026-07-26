"""Integration tests for the async download pipeline (HTTP mocked)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from fictionreaper.models import DownloadRequest
from fictionreaper.pipeline import download

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


def _chapter_html_for(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html><head>
<meta property="og:title" content="{title} - Mother of Learning" />
</head><body>
<h1>{title}</h1>
<div class="fic-header">
  <a href="/fiction/21220/mother-of-learning">Mother of Learning</a>
</div>
<div class="chapter-inner chapter-content">
<p>{body}</p>
</div>
</body></html>
"""


@pytest.mark.asyncio
async def test_download_fiction(
    fiction_html: str,
    tmp_path: Path,
) -> None:
    with respx.mock(assert_all_called=False) as router:
        router.get(FICTION_URL).mock(
            return_value=httpx.Response(200, text=fiction_html)
        )
        router.get(CHAPTER_URL).mock(
            return_value=httpx.Response(
                200,
                text=_chapter_html_for("1. Good Morning Brother", "Body one."),
            )
        )
        router.get(CHAPTER2_URL).mock(
            return_value=httpx.Response(
                200,
                text=_chapter_html_for("2. Life's Little Problems", "Body two."),
            )
        )
        router.get(CHAPTER3_URL).mock(
            return_value=httpx.Response(
                200,
                text=_chapter_html_for("3. The Bitter Truth", "Body three."),
            )
        )
        request = DownloadRequest(
            url=FICTION_URL,  # type: ignore[arg-type]
            output_dir=tmp_path,
            delay_seconds=0.0,
        )
        result = await download(request)

    assert result.fiction_id == 21220
    assert len(result.chapters) == 3
    assert result.output_dir == tmp_path / "mother-of-learning"
    for written in result.chapters:
        assert written.path.exists()
        assert "Body" in written.path.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_download_single_chapter(
    fiction_html: str,
    chapter_html: str,
    tmp_path: Path,
) -> None:
    with respx.mock(assert_all_called=False) as router:
        router.get(CHAPTER_URL).mock(
            return_value=httpx.Response(200, text=chapter_html)
        )
        router.get(FICTION_URL).mock(
            return_value=httpx.Response(200, text=fiction_html)
        )
        request = DownloadRequest(
            url=CHAPTER_URL,  # type: ignore[arg-type]
            output_dir=tmp_path,
            delay_seconds=0.0,
        )
        result = await download(request)

    assert len(result.chapters) == 1
    assert result.chapters[0].path.name.startswith("0001-")
    assert result.chapters[0].path.exists()
