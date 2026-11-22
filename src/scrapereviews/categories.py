"""Categories API: category tree and company rankings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ._base import clean_params, segment
from .models import CategoriesResponse, CategoryCompaniesResponse

if TYPE_CHECKING:
    from ._async_client import AsyncScrapeReviews
    from ._client import ScrapeReviews

CompanySort = Literal["relevant", "reviews_count"]
MinTrustScore = Literal["3.0", "4.0", "4.5"]


class CategoriesAPI:
    """``client.categories``: the category tree and company rankings per category."""

    def __init__(self, client: ScrapeReviews):
        self._client = client

    def list(self) -> CategoriesResponse:
        """All Trustpilot categories with their subcategories. Cost: 1 credit."""
        return CategoriesResponse.from_dict(self._client._get("/v1/categories"))

    def companies(
        self,
        category_id: str,
        country: str,
        sort: CompanySort = "relevant",
        min_trust_score: MinTrustScore | None = None,
        location: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> CategoryCompaniesResponse:
        """Company ranking of a category in a country. Cost: 1 credit per 10 companies (min 1).

        Args:
            category_id: Category id from :meth:`list`, e.g. ``"bank"``.
            country: ISO 3166-1 alpha-2 code, e.g. ``"IT"``.
            sort: ``"relevant"`` or ``"reviews_count"``.
            min_trust_score: ``"3.0"``, ``"4.0"`` or ``"4.5"``.
            location: City, e.g. ``"Milano"``.
            limit: Companies per page, 1-100.
            cursor: ``meta.next_cursor`` of the previous page.
        """
        return CategoryCompaniesResponse.from_dict(
            self._client._get(
                f"/v1/categories/{segment(category_id)}/companies",
                _company_params(country, sort, min_trust_score, location, limit, cursor),
            )
        )


class AsyncCategoriesAPI:
    """Async ``client.categories``."""

    def __init__(self, client: AsyncScrapeReviews):
        self._client = client

    async def list(self) -> CategoriesResponse:
        """All Trustpilot categories with their subcategories. Cost: 1 credit."""
        return CategoriesResponse.from_dict(await self._client._get("/v1/categories"))

    async def companies(
        self,
        category_id: str,
        country: str,
        sort: CompanySort = "relevant",
        min_trust_score: MinTrustScore | None = None,
        location: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> CategoryCompaniesResponse:
        """Company ranking of a category in a country. See :meth:`CategoriesAPI.companies`."""
        return CategoryCompaniesResponse.from_dict(
            await self._client._get(
                f"/v1/categories/{segment(category_id)}/companies",
                _company_params(country, sort, min_trust_score, location, limit, cursor),
            )
        )


def _company_params(
    country: str,
    sort: str,
    min_trust_score: str | None,
    location: str | None,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    return clean_params(
        {
            "country": country,
            "sort": sort,
            "min_trust_score": min_trust_score,
            "location": location,
            "limit": limit,
            "cursor": cursor,
        }
    )
