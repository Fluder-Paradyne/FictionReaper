"""Tests for the FastAPI app."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from fictionreaper.api import app

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


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_download_endpoint(
    client: TestClient,
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
        response = client.post(
            "/download",
            json={
                "url": FICTION_URL,
                "output_dir": str(tmp_path),
                "delay_seconds": 0.0,
            },
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["chapter_count"] == 3
    assert payload["fiction_id"] == 21220
    assert len(payload["chapters"]) == 3


def test_download_invalid_url(client: TestClient) -> None:
    response = client.post(
        "/download",
        json={"url": "https://example.com/not-rr", "delay_seconds": 0.0},
    )
    assert response.status_code == 422
