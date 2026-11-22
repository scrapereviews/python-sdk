"""Tests for the asynchronous client."""

from __future__ import annotations

import httpx
import pytest
import pytest_asyncio

from scrapereviews import AsyncScrapeReviews, NotFoundError, RateLimitError

from .payloads import company, company_summary, list_meta, reviews_page


@pytest_asyncio.fixture
async def client(mock_api, base_url, api_key):
    c = AsyncScrapeReviews(api_key=api_key, base_url=base_url)
    yield c
    await c.close()


async def test_search(client, mock_api):
    mock_api.get("/v1/companies/search", params={"query": "zalando"}).respond(
        200, json={"data": [company_summary()], "meta": list_meta(1)}
    )
    result = await client.companies.search("zalando")
    assert result.data[0].name == "Zalando"


async def test_get(client, mock_api):
    mock_api.get("/v1/companies/www.monzo.com").respond(
        200, json={"data": company(), "meta": {"credits_used": 2}}, headers={"X-Credits-Used": "2"}
    )
    result = await client.companies.get("www.monzo.com")
    assert result.data.name == "Monzo"
    assert client.credits_used == 2


async def test_iter_reviews(client, mock_api):
    route = mock_api.get("/v1/companies/zalando.it/reviews")
    route.side_effect = [
        httpx.Response(200, json=reviews_page(["a"], next_cursor="c1")),
        httpx.Response(200, json=reviews_page(["b", "c"])),
    ]
    ids = [r.id async for r in client.companies.iter_reviews("zalando.it")]
    assert ids == ["a", "b", "c"]
    assert route.calls[1].request.url.params["cursor"] == "c1"


async def test_categories(client, mock_api):
    mock_api.get("/v1/categories").respond(
        200, json={"data": [{"id": "bank", "name": "Bank"}], "meta": {"credits_used": 1}}
    )
    mock_api.get("/v1/categories/bank/companies", params={"country": "GB"}).respond(
        200,
        json={
            "category": {"id": "bank", "name": None, "country": "GB"},
            "data": [],
            "meta": list_meta(0),
        },
    )
    assert (await client.categories.list()).data[0].subcategories == []
    assert (await client.categories.companies("bank", "GB")).category.name is None


async def test_not_found(client, mock_api):
    mock_api.get("/v1/companies/nope.invalid").respond(
        404, json={"detail": {"error": "company_not_found", "message": "No profile"}}
    )
    with pytest.raises(NotFoundError) as exc_info:
        await client.companies.get("nope.invalid")
    assert exc_info.value.code == "company_not_found"


async def test_retries_rate_limit(client, mock_api, no_sleep):
    route = mock_api.get("/v1/categories")
    route.side_effect = [
        httpx.Response(
            429,
            json={"detail": {"error": "rate_limit_exceeded", "message": "slow"}},
            headers={"Retry-After": "3"},
        ),
        httpx.Response(200, json={"data": [], "meta": {"credits_used": 1}}),
    ]
    await client.categories.list()
    assert no_sleep == [3.0]


async def test_gives_up_after_retries(client, mock_api, no_sleep):
    mock_api.get("/v1/categories").respond(
        429,
        json={"detail": {"error": "rate_limit_exceeded", "message": "slow"}},
        headers={"Retry-After": "1"},
    )
    with pytest.raises(RateLimitError) as exc_info:
        await client.categories.list()
    assert exc_info.value.retry_after == 1.0
    assert no_sleep == [1.0, 1.0]


async def test_context_manager(mock_api, base_url, api_key):
    mock_api.get("/health").respond(200, json={"status": "healthy"})
    async with AsyncScrapeReviews(api_key=api_key, base_url=base_url) as client:
        assert (await client.health_check())["status"] == "healthy"
