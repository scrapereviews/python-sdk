"""Exceptions raised by the ScrapeReviews SDK."""

from __future__ import annotations

import httpx


class ScrapeReviewsError(Exception):
    """Base error for the ScrapeReviews API.

    Attributes:
        message: Human-readable message from the API.
        status_code: HTTP status, or None for errors raised before any request.
        code: Machine-readable API error code (e.g. ``company_not_found``), if any.
        retry_after: Seconds to wait before retrying, when the API says so.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        code: str | None = None,
        retry_after: float | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.retry_after = retry_after
        super().__init__(message)


class InvalidParameterError(ScrapeReviewsError):
    """A parameter was rejected (bad domain, stars, language, date...). HTTP 400."""


class AuthenticationError(ScrapeReviewsError):
    """Missing or invalid API key. HTTP 401."""


class InsufficientCreditsError(ScrapeReviewsError):
    """The credit balance is empty. HTTP 402, or 429 while the key is in cooldown."""


class NotFoundError(ScrapeReviewsError):
    """Company or category not found (``code`` tells which). HTTP 404."""


class InvalidCursorError(ScrapeReviewsError):
    """The cursor is malformed, tampered with, or was made for other filters. HTTP 422."""


class RateLimitError(ScrapeReviewsError):
    """Too many requests; ``retry_after`` holds the wait in seconds. HTTP 429."""


class UpstreamError(ScrapeReviewsError):
    """Trustpilot is unreachable, blocking, slow, or changed its pages. HTTP 502/503/504."""


_ERROR_MAP: dict[str, type[ScrapeReviewsError]] = {
    "invalid_parameter": InvalidParameterError,
    "missing_api_key": AuthenticationError,
    "invalid_api_key": AuthenticationError,
    "insufficient_credits": InsufficientCreditsError,
    "insufficient_credits_retry_later": InsufficientCreditsError,
    "company_not_found": NotFoundError,
    "category_not_found": NotFoundError,
    "invalid_cursor": InvalidCursorError,
    "rate_limit_exceeded": RateLimitError,
    "upstream_changed": UpstreamError,
    "upstream_blocked": UpstreamError,
    "upstream_error": UpstreamError,
    "upstream_timeout": UpstreamError,
}

_STATUS_MAP: dict[int, type[ScrapeReviewsError]] = {
    400: InvalidParameterError,
    401: AuthenticationError,
    402: InsufficientCreditsError,
    404: NotFoundError,
    422: InvalidCursorError,
    429: RateLimitError,
    502: UpstreamError,
    503: UpstreamError,
    504: UpstreamError,
}


def error_from_response(response: httpx.Response) -> ScrapeReviewsError:
    """Build the exception matching an error response."""
    message = f"HTTP {response.status_code}"
    code: str | None = None
    retry_after: float | None = None
    try:
        body = response.json()
    except ValueError:
        body = None
        message = response.text or message
    if isinstance(body, dict):
        detail = body.get("detail", body)
        if isinstance(detail, dict):
            code = detail.get("error")
            message = detail.get("message", message)
            retry_after = _to_seconds(detail.get("retry_after"))
        elif isinstance(detail, str):
            message = detail
    header_retry = _to_seconds(response.headers.get("retry-after"))
    if header_retry is not None:
        retry_after = header_retry

    exc_class = _ERROR_MAP.get(code or "") or _STATUS_MAP.get(response.status_code)
    return (exc_class or ScrapeReviewsError)(
        message, status_code=response.status_code, code=code, retry_after=retry_after
    )


def _to_seconds(value: object) -> float | None:
    try:
        return float(value) if value is not None else None  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
