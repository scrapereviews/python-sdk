"""Tests for error mapping and retries."""

from __future__ import annotations

import httpx
import pytest

from scrapereviews import (
    AuthenticationError,
    InsufficientCreditsError,
    InvalidCursorError,
    InvalidParameterError,
    NotFoundError,
    RateLimitError,
    ScrapeReviews,
    ScrapeReviewsError,
    UpstreamError,
)


@pytest.fixture
def client(mock_api, api_key, base_url):
    c = ScrapeReviews(api_key=api_key, base_url=base_url)
    yield c
    c.close()


def error(status: int, code: str, message: str = "boom", headers=None) -> httpx.Response:
    return httpx.Response(
        status, json={"detail": {"error": code, "message": message}}, headers=headers
    )


@pytest.mark.parametrize(
    ("status", "code", "exc_class"),
    [
        (400, "invalid_parameter", InvalidParameterError),
        (401, "missing_api_key", AuthenticationError),
        (401, "invalid_api_key", AuthenticationError),
        (402, "insufficient_credits", InsufficientCreditsError),
        (404, "company_not_found", NotFoundError),
        (404, "category_not_found", NotFoundError),
        (422, "invalid_cursor", InvalidCursorError),
        (502, "upstream_changed", UpstreamError),
    ],
)
def test_error_codes(client, mock_api, no_sleep, status, code, exc_class):
    mock_api.get("/v1/companies/x.com").mock(return_value=error(status, code, "Nope"))
    with pytest.raises(exc_class) as exc_info:
        client.companies.get("x.com")
    assert exc_info.value.status_code == status
    assert exc_info.value.code == code
    assert exc_info.value.message == "Nope"
    assert no_sleep == []


@pytest.mark.parametrize(
    ("status", "code"),
    [(503, "upstream_blocked"), (503, "upstream_error"), (504, "upstream_timeout")],
)
def test_upstream_errors_retried_then_raised(client, mock_api, no_sleep, status, code):
    route = mock_api.get("/v1/companies/x.com").mock(return_value=error(status, code))
    with pytest.raises(UpstreamError):
        client.companies.get("x.com")
    assert route.call_count == 3
    assert no_sleep == [0.5, 1.0]


def test_retry_then_success(client, mock_api, no_sleep):
    route = mock_api.get("/v1/categories")
    route.side_effect = [
        error(503, "upstream_blocked"),
        httpx.Response(
            200, json={"data": [], "meta": {"credits_used": 1}}, headers={"X-Credits-Used": "1"}
        ),
    ]
    client.categories.list()
    assert client.credits_used == 1
    assert no_sleep == [0.5]


def test_rate_limit_retry_after(client, mock_api, no_sleep):
    mock_api.get("/v1/categories").mock(
        return_value=error(429, "rate_limit_exceeded", headers={"Retry-After": "2"})
    )
    with pytest.raises(RateLimitError) as exc_info:
        client.categories.list()
    assert exc_info.value.retry_after == 2.0
    assert no_sleep == [2.0, 2.0]


def test_retry_after_from_body(client, mock_api, no_sleep):
    mock_api.get("/v1/categories").mock(
        return_value=httpx.Response(
            429,
            json={"detail": {"error": "rate_limit_exceeded", "message": "x", "retry_after": 4}},
        )
    )
    with pytest.raises(RateLimitError):
        client.categories.list()
    assert no_sleep == [4.0, 4.0]


def test_long_retry_after_not_waited(client, mock_api, no_sleep):
    mock_api.get("/v1/categories").mock(
        return_value=error(429, "rate_limit_exceeded", headers={"Retry-After": "600"})
    )
    with pytest.raises(RateLimitError) as exc_info:
        client.categories.list()
    assert exc_info.value.retry_after == 600.0
    assert no_sleep == []


def test_no_credit_cooldown_not_retried(client, mock_api, no_sleep):
    mock_api.get("/v1/categories").mock(
        return_value=error(429, "insufficient_credits_retry_later", headers={"Retry-After": "5"})
    )
    with pytest.raises(InsufficientCreditsError) as exc_info:
        client.categories.list()
    assert exc_info.value.retry_after == 5.0
    assert no_sleep == []


def test_max_retries_zero(mock_api, api_key, base_url, no_sleep):
    route = mock_api.get("/v1/categories").mock(return_value=error(500, "internal_error"))
    with ScrapeReviews(api_key=api_key, base_url=base_url, max_retries=0) as client:
        with pytest.raises(ScrapeReviewsError) as exc_info:
            client.categories.list()
    assert type(exc_info.value) is ScrapeReviewsError
    assert route.call_count == 1


def test_status_fallback_without_json(client, mock_api):
    mock_api.get("/v1/companies/x.com").mock(return_value=httpx.Response(404, text="Not Found"))
    with pytest.raises(NotFoundError) as exc_info:
        client.companies.get("x.com")
    assert exc_info.value.message == "Not Found"
    assert exc_info.value.code is None


def test_exception_hierarchy():
    for cls in (
        AuthenticationError,
        InsufficientCreditsError,
        InvalidCursorError,
        InvalidParameterError,
        NotFoundError,
        RateLimitError,
        UpstreamError,
    ):
        assert issubclass(cls, ScrapeReviewsError)
