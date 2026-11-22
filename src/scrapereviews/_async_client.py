"""Asynchronous ScrapeReviews client."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from ._base import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    build_headers,
    credits_from,
    resolve_api_key,
    resolve_base_url,
    retry_delay,
)
from .categories import AsyncCategoriesAPI
from .companies import AsyncCompaniesAPI
from .errors import error_from_response


class AsyncScrapeReviews:
    """
    Asynchronous client for the ScrapeReviews API.

    Usage:
        async with AsyncScrapeReviews(api_key="YOUR_API_KEY") as client:
            company = (await client.companies.get("zalando.it")).data
            async for review in client.companies.iter_reviews("zalando.it", max_reviews=200):
                print(review.rating, review.title)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """Same arguments as :class:`ScrapeReviews`."""
        self.api_key = resolve_api_key(api_key)
        self.base_url = resolve_base_url(base_url)
        self.timeout = timeout
        self.max_retries = max_retries

        self._http = httpx.AsyncClient(
            base_url=self.base_url, headers=build_headers(self.api_key), timeout=timeout
        )
        self._last_response: httpx.Response | None = None

        self.companies = AsyncCompaniesAPI(self)
        self.categories = AsyncCategoriesAPI(self)

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        attempt = 0
        while True:
            response = await self._http.get(path, params=params)
            self._last_response = response
            if response.is_success:
                return response.json()
            error = error_from_response(response)
            delay = retry_delay(error, attempt, self.max_retries)
            if delay is None:
                raise error
            await asyncio.sleep(delay)
            attempt += 1

    @property
    def credits_used(self) -> int | None:
        """Credits charged by the last request (``X-Credits-Used`` header)."""
        return credits_from(self._last_response)

    async def health_check(self) -> dict[str, Any]:
        """Check API health status (no authentication, no credits)."""
        return (await self._http.get("/health")).json()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> AsyncScrapeReviews:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
