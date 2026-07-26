"""Async HTTP fetching for Royal Road pages."""

from __future__ import annotations

import asyncio
from types import TracebackType
from typing import Self

import httpx

from fictionreaper.exceptions import FetchError


class AsyncFetcher:
    """Thin async HTTP client with polite delay between requests."""

    def __init__(
        self,
        *,
        user_agent: str,
        delay_seconds: float = 1.0,
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._user_agent: str = user_agent
        self._delay_seconds: float = delay_seconds
        self._timeout_seconds: float = timeout_seconds
        self._owns_client: bool = client is None
        self._client: httpx.AsyncClient = client or httpx.AsyncClient(
            headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"},
            follow_redirects=True,
            timeout=timeout_seconds,
        )
        self._request_count: int = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying client if this fetcher owns it."""
        if self._owns_client:
            await self._client.aclose()

    async def get_text(self, url: str) -> str:
        """GET ``url`` and return response text.

        Applies a delay before the 2nd and subsequent requests when
        ``delay_seconds`` > 0.

        Raises:
            FetchError: On network failure or non-success status.
        """
        if self._request_count > 0 and self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)
        self._request_count += 1
        try:
            response: httpx.Response = await self._client.get(url)
        except httpx.HTTPError as exc:
            raise FetchError(f"Request failed for {url}: {exc}") from exc
        if response.status_code >= 400:
            raise FetchError(f"HTTP {response.status_code} for {url}")
        text: str = response.text
        return text
