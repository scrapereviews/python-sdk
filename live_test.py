#!/usr/bin/env python3
"""
Manual live test of every ScrapeReviews endpoint (spends a few credits, ~15).

Results are saved as JSON files in output/ for inspection.

Usage:
    SCRAPEREVIEWS_API_KEY=... python live_test.py
    SCRAPEREVIEWS_API_KEY=... SCRAPEREVIEWS_BASE_URL=http://localhost:8000 python live_test.py
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from scrapereviews import ScrapeReviews, ScrapeReviewsError

DOMAIN = "www.monzo.com"
CATEGORY = "bank"
COUNTRY = "GB"

OUTPUT_DIR = Path(__file__).parent / "output"


def run(name: str, client: ScrapeReviews, call: Callable[[], Any]) -> Any:
    try:
        result = call()
    except ScrapeReviewsError as e:
        print(f"  [FAIL] {name}: {type(e).__name__} {e.status_code} {e.code} - {e.message}")
        return None
    OUTPUT_DIR.mkdir(exist_ok=True)
    data = asdict(result) if is_dataclass(result) else result
    path = OUTPUT_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    print(f"  [OK]   {name} (credits used: {client.credits_used}) -> output/{path.name}")
    return result


def main() -> int:
    try:
        client = ScrapeReviews()
    except ScrapeReviewsError as e:
        print(e.message)
        return 1

    print(f"API: {client.base_url}\n")
    with client:
        run("health", client, client.health_check)
        run("search", client, lambda: client.companies.search("monzo", limit=5))
        run("company", client, lambda: client.companies.get(DOMAIN, include_similar=True))
        page = run(
            "reviews_negative",
            client,
            lambda: client.companies.reviews(DOMAIN, stars=[1, 2], language="en", limit=10),
        )
        if page and page.meta.next_cursor:
            run(
                "reviews_negative_page2",
                client,
                lambda: client.companies.reviews(
                    DOMAIN, stars=[1, 2], language="en", limit=10, cursor=page.meta.next_cursor
                ),
            )
        run(
            "reviews_iter",
            client,
            lambda: [asdict(r) for r in client.companies.iter_reviews(DOMAIN, max_reviews=25)],
        )
        run("categories", client, client.categories.list)
        run(
            "category_companies",
            client,
            lambda: client.categories.companies(CATEGORY, COUNTRY, limit=10),
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
