# ScrapeReviews Python SDK

Official Python SDK for the [ScrapeReviews](https://scrapereviews.com) API — Trustpilot company profiles, reviews and category rankings as clean JSON.

## Installation

```bash
pip install scrapereviews
```

## Quick Start

```python
from scrapereviews import ScrapeReviews

client = ScrapeReviews(api_key="YOUR_API_KEY")  # or set SCRAPEREVIEWS_API_KEY

# Company profile
company = client.companies.get("zalando.it").data
print(company.name, company.trust_score, company.review_count)

# Latest negative reviews
page = client.companies.reviews("zalando.it", stars=[1, 2], limit=20)
for review in page.data:
    print(review.rating, review.title, review.published_at)
```

## Async Usage

```python
import asyncio
from scrapereviews import AsyncScrapeReviews

async def main():
    async with AsyncScrapeReviews() as client:
        async for review in client.companies.iter_reviews("zalando.it", max_reviews=200):
            print(review.rating, review.text)

asyncio.run(main())
```

## Configuration

| Argument | Environment variable | Default |
|----------|----------------------|---------|
| `api_key` | `SCRAPEREVIEWS_API_KEY` | required |
| `base_url` | `SCRAPEREVIEWS_BASE_URL` | `https://api.scrapereviews.com` |
| `timeout` | — | `60` seconds |
| `max_retries` | — | `2` (rate limits and transient errors) |

## API Reference

All methods return typed dataclasses (`scrapereviews.models`). Lists come with a `meta`
(`credits_used`, `cache_hit`, `count`, `total`, `has_more`, `next_cursor`): pass
`meta.next_cursor` as `cursor` to get the next page.

### Companies

```python
# Search by name or domain (1 credit per 10 results)
results = client.companies.search("zalando", limit=10)
next_page = client.companies.search("zalando", cursor=results.meta.next_cursor)

# Full profile (2 credits). Accepts a domain, a website URL or a Trustpilot URL.
company = client.companies.get("https://www.trustpilot.com/review/zalando.it", include_similar=True)

# One page of reviews (1 credit per 5 reviews)
page = client.companies.reviews(
    "zalando.it",
    stars=[1, 2],            # or "1,2"
    language="it",           # "all" or ISO 639-1
    since="2026-01-01",      # date or YYYY-MM-DD / ISO 8601
    until=None,
    verified=False,
    with_reply=False,
    search="refund",
    sort="recent",           # or "relevant"
    limit=100,               # 1-100
)

# Every matching review, page by page (each page is billed as it is fetched)
for review in client.companies.iter_reviews("zalando.it", stars=[1], max_reviews=500):
    ...
```

Trustpilot shows at most 200 reviews per filter combination; the API splits the query by
star rating and language to go further. `page.meta.complete` is `False` when a single
(star, language) slice still held more than 200 reviews.

### Categories

```python
# Category tree (1 credit)
tree = client.categories.list()

# Company ranking of a category in a country (1 credit per 10 companies)
ranking = client.categories.companies(
    "bank", "IT", sort="reviews_count", min_trust_score="4.0", location="Milano", limit=20
)
```

## Error Handling

```python
from scrapereviews import (
    ScrapeReviews,
    NotFoundError,
    InsufficientCreditsError,
    RateLimitError,
)

try:
    company = client.companies.get("does-not-exist.invalid")
except NotFoundError as e:
    print(e.code, e.message)       # company_not_found, ...
except InsufficientCreditsError:
    print("Top up your credits")
except RateLimitError as e:
    print(f"Retry in {e.retry_after}s")
```

### Exception Hierarchy

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| `ScrapeReviewsError` | — | Base exception (`message`, `status_code`, `code`, `retry_after`) |
| `InvalidParameterError` | 400 | Bad domain, stars, language, date... |
| `AuthenticationError` | 401 | Missing or invalid API key |
| `InsufficientCreditsError` | 402 / 429 | Credit balance is empty |
| `NotFoundError` | 404 | Company or category not found (`code` tells which) |
| `InvalidCursorError` | 422 | Cursor malformed or made for other filters |
| `RateLimitError` | 429 | Too many requests (`retry_after` seconds) |
| `UpstreamError` | 502 / 503 / 504 | Trustpilot unreachable, slow or changed |

Rate limits (429) and transient errors (500, 503, 504) are retried up to `max_retries` times,
honouring `Retry-After`. Failed calls cost no credits.

## Credits

Every response carries what it cost in `meta.credits_used`; the client also exposes the
`X-Credits-Used` header of the last request:

```python
client.companies.get("zalando.it")
print(client.credits_used)  # 2
```

## Development

```bash
uv venv -p 3.12 && uv pip install -e ".[dev]"
.venv/bin/pytest && .venv/bin/ruff check .

# Manual test against the live API (spends ~15 credits)
SCRAPEREVIEWS_API_KEY=... python live_test.py
```

## License

MIT
