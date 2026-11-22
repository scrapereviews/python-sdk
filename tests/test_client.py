"""Tests for the synchronous client: endpoints, params, models, pagination, headers."""

from __future__ import annotations

from datetime import date

import httpx
import pytest

from scrapereviews import (
    AuthenticationError,
    Company,
    Review,
    ScrapeReviews,
)
from scrapereviews._base import DEFAULT_BASE_URL

from .payloads import company, company_summary, list_meta, reviews_page


@pytest.fixture
def client(mock_api, api_key, base_url):
    c = ScrapeReviews(api_key=api_key, base_url=base_url, max_retries=0)
    yield c
    c.close()


class TestClientInit:
    def test_defaults(self, api_key):
        with ScrapeReviews(api_key=api_key) as client:
            assert client.api_key == api_key
            assert client.base_url == DEFAULT_BASE_URL

    def test_custom_base_url_strips_slash(self, api_key):
        with ScrapeReviews(api_key=api_key, base_url="https://custom.api.com/") as client:
            assert client.base_url == "https://custom.api.com"

    def test_env_vars(self, monkeypatch):
        monkeypatch.setenv("SCRAPEREVIEWS_API_KEY", "env_key")
        monkeypatch.setenv("SCRAPEREVIEWS_BASE_URL", "http://localhost:8000/")
        with ScrapeReviews() as client:
            assert client.api_key == "env_key"
            assert client.base_url == "http://localhost:8000"

    def test_missing_key(self):
        with pytest.raises(AuthenticationError, match="SCRAPEREVIEWS_API_KEY"):
            ScrapeReviews()

    def test_sends_api_key(self, client, mock_api, api_key):
        route = mock_api.get("/v1/categories").respond(200, json={"data": [], "meta": {}})
        client.categories.list()
        assert route.calls.last.request.headers["X-API-Key"] == api_key


class TestCompanies:
    def test_search(self, client, mock_api):
        route = mock_api.get(
            "/v1/companies/search", params={"query": "zalando", "limit": "5", "cursor": "c1"}
        ).respond(200, json={"data": [company_summary()], "meta": list_meta(1, "c2")})
        result = client.companies.search("zalando", limit=5, cursor="c1")
        assert route.called
        assert result.data[0].domain == "zalando.it"
        assert result.data[0].categories[0].id == "shoe_store"
        assert result.data[0].contact.city == "Berlin"
        assert result.meta.next_cursor == "c2"
        assert result.meta.has_more is True

    def test_get(self, client, mock_api):
        mock_api.get("/v1/companies/www.monzo.com", params={"include_similar": "true"}).respond(
            200, json={"data": company(), "meta": {"credits_used": 2, "cache_hit": True}}
        )
        result = client.companies.get("www.monzo.com", include_similar=True)
        assert isinstance(result.data, Company)
        assert result.data.star_distribution.five == 60833
        assert result.data.languages[0].language == "en"
        assert result.data.reply_behavior.reply_rate == 51.07
        assert result.meta.credits_used == 2
        assert result.meta.cache_hit is True

    def test_get_omits_false_flags(self, client, mock_api):
        route = mock_api.get("/v1/companies/monzo.com").respond(
            200, json={"data": company("monzo.com"), "meta": {"credits_used": 2}}
        )
        client.companies.get("monzo.com")
        assert "include_similar" not in str(route.calls.last.request.url)

    @pytest.mark.parametrize(
        "given",
        [
            "https://www.monzo.com/about?x=1",
            "https://www.trustpilot.com/review/www.monzo.com",
            "www.monzo.com/",
        ],
    )
    def test_get_accepts_urls(self, client, mock_api, given):
        route = mock_api.get("/v1/companies/www.monzo.com").respond(
            200, json={"data": company(), "meta": {"credits_used": 2}}
        )
        client.companies.get(given)
        assert route.called

    def test_reviews_params(self, client, mock_api):
        route = mock_api.get(
            "/v1/companies/zalando.it/reviews",
            params={
                "stars": "1,2",
                "language": "it",
                "since": "2026-01-01",
                "until": "2026-06-30",
                "verified": "true",
                "with_reply": "true",
                "search": "refund",
                "sort": "relevant",
                "limit": "50",
                "cursor": "abc",
            },
        ).respond(200, json=reviews_page(["r1"]))
        result = client.companies.reviews(
            "zalando.it",
            stars=[2, 1],
            language="it",
            since=date(2026, 1, 1),
            until="2026-06-30",
            verified=True,
            with_reply=True,
            search="refund",
            sort="relevant",
            limit=50,
            cursor="abc",
        )
        assert route.called
        assert result.company.domain == "zalando.it"
        assert isinstance(result.data[0], Review)
        assert result.data[0].author.id == "u_03c1"
        assert result.meta.complete is True

    def test_reviews_defaults(self, client, mock_api):
        route = mock_api.get("/v1/companies/zalando.it/reviews").respond(
            200, json=reviews_page(["r1"])
        )
        client.companies.reviews("zalando.it", stars="4,5")
        params = dict(route.calls.last.request.url.params)
        assert params == {"stars": "4,5", "sort": "recent", "limit": "20"}

    def test_iter_reviews_follows_cursor(self, client, mock_api):
        route = mock_api.get("/v1/companies/zalando.it/reviews")
        route.side_effect = [
            httpx.Response(200, json=reviews_page(["a", "b"], next_cursor="c1")),
            httpx.Response(200, json=reviews_page(["c"], next_cursor=None)),
        ]
        ids = [r.id for r in client.companies.iter_reviews("zalando.it", stars=[1])]
        assert ids == ["a", "b", "c"]
        first, second = (c.request.url.params for c in route.calls)
        assert "cursor" not in first and first["limit"] == "100"
        assert second["cursor"] == "c1" and second["stars"] == "1"

    def test_iter_reviews_max_reviews(self, client, mock_api):
        route = mock_api.get("/v1/companies/zalando.it/reviews")
        route.side_effect = [
            httpx.Response(200, json=reviews_page(["a", "b"], next_cursor="c1")),
            httpx.Response(200, json=reviews_page(["c"], next_cursor="c2")),
        ]
        reviews = list(client.companies.iter_reviews("zalando.it", page_size=2, max_reviews=3))
        assert [r.id for r in reviews] == ["a", "b", "c"]
        assert [c.request.url.params["limit"] for c in route.calls] == ["2", "1"]

    def test_reply_parsed(self, client, mock_api):
        page = reviews_page([])
        page["data"] = [
            {**reviews_page(["x"])["data"][0], "reply": {"text": "Sorry", "published_at": None}}
        ]
        mock_api.get("/v1/companies/zalando.it/reviews").respond(200, json=page)
        result = client.companies.reviews("zalando.it")
        assert result.data[0].reply is not None
        assert result.data[0].reply.text == "Sorry"


class TestCategories:
    def test_list(self, client, mock_api):
        mock_api.get("/v1/categories").respond(
            200,
            json={
                "data": [
                    {
                        "id": "animals_pets",
                        "name": "Animals & Pets",
                        "subcategories": [
                            {"id": "animal_health", "name": "Animal Health", "subcategories": []}
                        ],
                    }
                ],
                "meta": {"credits_used": 1, "cache_hit": False},
            },
        )
        result = client.categories.list()
        assert result.data[0].subcategories[0].id == "animal_health"
        assert result.meta.credits_used == 1

    def test_companies(self, client, mock_api):
        route = mock_api.get(
            "/v1/categories/bank/companies",
            params={
                "country": "IT",
                "sort": "reviews_count",
                "min_trust_score": "4.0",
                "location": "Milano",
                "limit": "10",
            },
        ).respond(
            200,
            json={
                "category": {"id": "bank", "name": "Bank", "country": "IT"},
                "data": [company_summary("bank.it")],
                "meta": list_meta(1),
            },
        )
        result = client.categories.companies(
            "bank", "IT", sort="reviews_count", min_trust_score="4.0", location="Milano", limit=10
        )
        assert route.called
        assert result.category.country == "IT"
        assert result.data[0].domain == "bank.it"
        assert result.meta.next_cursor is None


class TestResponseHeaders:
    def test_credits_used(self, client, mock_api):
        mock_api.get("/v1/companies/monzo.com").respond(
            200,
            json={"data": company("monzo.com"), "meta": {"credits_used": 2}},
            headers={"X-Credits-Used": "2"},
        )
        assert client.credits_used is None
        client.companies.get("monzo.com")
        assert client.credits_used == 2

    def test_health_check(self, client, mock_api):
        mock_api.get("/health").respond(200, json={"status": "healthy"})
        assert client.health_check() == {"status": "healthy"}
