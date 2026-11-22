"""Shared configuration and helpers for the sync and async clients."""

from __future__ import annotations

import os
from datetime import date
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from .errors import AuthenticationError, ScrapeReviewsError

__version__ = "0.1.0"

DEFAULT_BASE_URL = "https://api.scrapereviews.com"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2
MAX_RETRY_DELAY = 30.0
USER_AGENT = f"ScrapeReviews-Python/{__version__}"

API_KEY_ENV = "SCRAPEREVIEWS_API_KEY"
BASE_URL_ENV = "SCRAPEREVIEWS_BASE_URL"

# 502 (upstream_changed) is not retried: Trustpilot changed its pages and an immediate
# retry gets the same answer.
RETRYABLE_STATUS = {429, 500, 503, 504}


def resolve_api_key(api_key: str | None) -> str:
    key = api_key or os.environ.get(API_KEY_ENV, "")
    if not key:
        raise AuthenticationError(
            f"No API key: pass api_key=... or set the {API_KEY_ENV} environment variable."
        )
    return key


def resolve_base_url(base_url: str | None) -> str:
    return (base_url or os.environ.get(BASE_URL_ENV) or DEFAULT_BASE_URL).rstrip("/")


def build_headers(api_key: str) -> dict[str, str]:
    return {"X-API-Key": api_key, "Accept": "application/json", "User-Agent": USER_AGENT}


def retry_delay(error: ScrapeReviewsError, attempt: int, max_retries: int) -> float | None:
    """Seconds to wait before retrying ``error``, or None if it must be raised.

    Only rate limits and transient server/upstream errors are retried. A 429 caused by an
    empty balance (``insufficient_credits_retry_later``) is not: waiting does not add credits.
    Failed calls cost no credits, so retries are free.
    """
    if attempt >= max_retries or error.status_code not in RETRYABLE_STATUS:
        return None
    if error.code == "insufficient_credits_retry_later":
        return None
    if error.retry_after is not None:
        return error.retry_after if error.retry_after <= MAX_RETRY_DELAY else None
    return min(0.5 * 2**attempt, MAX_RETRY_DELAY)


def domain_path(domain: str) -> str:
    """Path segment for a company domain.

    URLs (``https://www.example.com/page``, ``https://www.trustpilot.com/review/example.com``)
    are reduced to the domain here, because a slash cannot travel inside a path segment.
    """
    value = domain.strip()
    if "://" in value:
        parsed = urlparse(value)
        host = parsed.hostname or ""
        if host.endswith("trustpilot.com") and parsed.path.startswith("/review/"):
            value = parsed.path.split("/review/", 1)[1]
        else:
            value = host
    value = value.split("/")[0].split("?")[0].split("#")[0]
    if not value:
        raise ValueError(f"'{domain}' is not a valid domain")
    return quote(value, safe="")


def segment(value: str) -> str:
    """Percent-encode a single path segment (category ids)."""
    return quote(value.strip(), safe="")


def clean_params(params: dict[str, Any]) -> dict[str, Any]:
    """Drop unset values, send booleans only when true, serialize dates and star lists."""
    out: dict[str, Any] = {}
    for key, value in params.items():
        if value is None or value is False:
            continue
        if value is True:
            out[key] = "true"
        elif isinstance(value, date):
            out[key] = value.isoformat()
        elif isinstance(value, (list, tuple, set)):
            out[key] = ",".join(str(v) for v in sorted(value))
        else:
            out[key] = value
    return out


def credits_from(response: httpx.Response | None) -> int | None:
    if response is None:
        return None
    value = response.headers.get("x-credits-used")
    return int(value) if value and value.isdigit() else None
