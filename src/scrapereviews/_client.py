"""Synchronous ScrapeReviews client."""

from __future__ import annotations

import time
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
from .categories import CategoriesAPI
from .companies import CompaniesAPI
from .errors import error_from_response


class ScrapeReviews:
    """
    Synchronous client for the ScrapeReviews API (Trustpilot companies and reviews).

    Usage:
        client = ScrapeReviews(api_key="YOUR_API_KEY")  # or set SCRAPEREVIEWS_API_KEY
        company = client.companies.get("zalando.it").data

        with ScrapeReviews() as client:
            for review in client.companies.iter_reviews("zalando.it", stars=[1, 2]):
                print(review.rating, review.title)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """
        Args:
            api_key: API key. Defaults to the ``SCRAPEREVIEWS_API_KEY`` environment variable.
            base_url: API base URL. Defaults to ``SCRAPEREVIEWS_BASE_URL`` or the public API.
            timeout: Request timeout in seconds (review pages can take a while upstream).
            max_retries: Retries on rate limits and transient server/upstream errors.
        """
        self.api_key = resolve_api_key(api_key)
        self.base_url = resolve_base_url(base_url)
        self.timeout = timeout
        self.max_retries = max_retries

        self._http = httpx.Client(
            base_url=self.base_url, headers=build_headers(self.api_key), timeout=timeout
        )
        self._last_response: httpx.Response | None = None

        self.companies = CompaniesAPI(self)
        self.categories = CategoriesAPI(self)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        attempt = 0
        while True:
            response = self._http.get(path, params=params)
            self._last_response = response
            if response.is_success:
                return response.json()
            error = error_from_response(response)
            delay = retry_delay(error, attempt, self.max_retries)
            if delay is None:
                raise error
            time.sleep(delay)
            attempt += 1

    @property
    def credits_used(self) -> int | None:
        """Credits charged by the last request (``X-Credits-Used`` header)."""
        return credits_from(self._last_response)

    def health_check(self) -> dict[str, Any]:
        """Check API health status (no authentication, no credits)."""
        return self._http.get("/health").json()

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self) -> ScrapeReviews:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
