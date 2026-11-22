"""Sample API payloads shared by the tests."""

from __future__ import annotations

from typing import Any


def company_summary(domain: str = "zalando.it") -> dict[str, Any]:
    return {
        "id": "4e806c830000640005111892",
        "domain": domain,
        "name": "Zalando",
        "trust_score": 1.9,
        "stars": 2.0,
        "review_count": 13683,
        "logo_url": None,
        "categories": [{"id": "shoe_store", "name": "Shoe Store", "is_primary": False}],
        "contact": {"website": "https://zalando.it", "city": "Berlin", "country": "Germany"},
        "trustpilot_url": f"https://www.trustpilot.com/review/{domain}",
    }


def company(domain: str = "www.monzo.com") -> dict[str, Any]:
    return {
        "id": "abc",
        "domain": domain,
        "name": "Monzo",
        "website": "https://www.monzo.com",
        "trust_score": 4.6,
        "stars": 4.5,
        "review_count": 74600,
        "review_count_last_12_months": 9000,
        "star_distribution": {"one": 7462, "two": 856, "three": 1069, "four": 4380, "five": 60833},
        "languages": [{"language": "en", "count": 70000}],
        "categories": [{"id": "bank", "name": "Bank", "is_primary": True}],
        "description": "Banking",
        "country": "GB",
        "contact": {"email": "help@monzo.com", "country": "United Kingdom"},
        "is_claimed": True,
        "claimed_at": "2015-02-18T19:08:43.000Z",
        "is_closed": False,
        "is_temporarily_closed": False,
        "is_using_paid_features": True,
        "reply_behavior": {"reply_rate": 51.07, "average_days_to_reply": 2.9},
        "verified": False,
        "consumer_alert": None,
        "logo_url": "https://example.com/logo.png",
        "similar": [],
        "trustpilot_url": f"https://www.trustpilot.com/review/{domain}",
        "some_future_field": 1,
    }


def review(review_id: str = "r1", rating: int = 1, reply: bool = False) -> dict[str, Any]:
    return {
        "id": review_id,
        "rating": rating,
        "title": "Bad",
        "text": "Never arrived",
        "language": "it",
        "experienced_at": "2026-11-19T00:00:00.000Z",
        "published_at": "2026-11-20T01:05:15.000Z",
        "updated_at": None,
        "is_verified": False,
        "verification_source": "invitation",
        "source": "Organic",
        "likes": 0,
        "author": {"id": "u_03c1", "country": "IT", "review_count": 2, "is_verified": False},
        "reply": {"text": "Sorry", "published_at": "2026-11-21T00:00:00Z"} if reply else None,
        "url": f"https://www.trustpilot.com/reviews/{review_id}",
    }


def list_meta(count: int, next_cursor: str | None = None, credits: int = 1) -> dict[str, Any]:
    return {
        "credits_used": credits,
        "cache_hit": False,
        "count": count,
        "total": 100,
        "has_more": next_cursor is not None,
        "next_cursor": next_cursor,
    }


def reviews_page(ids: list[str], next_cursor: str | None = None) -> dict[str, Any]:
    return {
        "company": {
            "id": "4e80",
            "domain": "zalando.it",
            "name": "Zalando",
            "trust_score": 1.9,
            "review_count": 13683,
            "trustpilot_url": "https://www.trustpilot.com/review/zalando.it",
        },
        "data": [review(i) for i in ids],
        "meta": {**list_meta(len(ids), next_cursor), "complete": True},
    }
