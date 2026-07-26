"""Tests for AsyncFetcher."""

from __future__ import annotations

import httpx
import pytest
import respx

from fictionreaper.exceptions import FetchError
from fictionreaper.fetch import AsyncFetcher


@pytest.mark.asyncio
async def test_get_text_success() -> None:
    url = "https://www.royalroad.com/fiction/1/x"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, text="hello"))
        async with AsyncFetcher(user_agent="test", delay_seconds=0.0) as fetcher:
            text = await fetcher.get_text(url)
    assert text == "hello"


@pytest.mark.asyncio
async def test_get_text_http_error() -> None:
    url = "https://www.royalroad.com/fiction/1/x"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(404, text="nope"))
        async with AsyncFetcher(user_agent="test", delay_seconds=0.0) as fetcher:
            with pytest.raises(FetchError, match="404"):
                await fetcher.get_text(url)
