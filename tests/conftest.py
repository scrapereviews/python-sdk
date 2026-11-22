"""Shared test fixtures."""

from __future__ import annotations

import pytest
import respx

BASE_URL = "https://api.test.scrapereviews.com"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("SCRAPEREVIEWS_API_KEY", raising=False)
    monkeypatch.delenv("SCRAPEREVIEWS_BASE_URL", raising=False)


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def api_key():
    return "test_key_for_unit_tests"


@pytest.fixture
def mock_api(base_url):
    with respx.mock(base_url=base_url, assert_all_called=False) as mock:
        yield mock


@pytest.fixture
def no_sleep(monkeypatch):
    """Record retry waits instead of sleeping."""
    waits: list[float] = []
    monkeypatch.setattr("scrapereviews._client.time.sleep", waits.append)

    async def fake_async_sleep(delay: float) -> None:
        waits.append(delay)

    monkeypatch.setattr("scrapereviews._async_client.asyncio.sleep", fake_async_sleep)
    return waits
