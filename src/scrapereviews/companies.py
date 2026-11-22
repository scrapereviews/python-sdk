"""Companies API: search, profile, reviews."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Iterator
from datetime import date
from typing import TYPE_CHECKING, Any, Literal, Union

from ._base import clean_params, domain_path
from .models import CompanyResponse, Review, ReviewsResponse, SearchResponse

if TYPE_CHECKING:
    from ._async_client import AsyncScrapeReviews
    from ._client import ScrapeReviews

Stars = Union[Iterable[int], str, None]
DateLike = Union[date, str, None]
ReviewSort = Literal["recent", "relevant"]


class CompaniesAPI:
    """``client.companies``: search companies, read profiles and reviews."""

    def __init__(self, client: ScrapeReviews):
        self._client = client

    def search(self, query: str, limit: int = 10, cursor: str | None = None) -> SearchResponse:
        """Search Trustpilot companies by name or domain.

        An exact domain returns that company. Cost: 1 credit per 10 results (min 1).

        Args:
            query: Company name or domain.
            limit: Results per page, 1-50.
            cursor: ``meta.next_cursor`` of the previous page.
        """
        params = clean_params({"query": query, "limit": limit, "cursor": cursor})
        return SearchResponse.from_dict(self._client._get("/v1/companies/search", params))

    def get(self, domain: str, include_similar: bool = False) -> CompanyResponse:
        """Full company profile. Cost: 2 credits.

        Args:
            domain: ``example.com``, ``www.example.com``, a website URL or a Trustpilot URL.
            include_similar: Also return similar companies in ``data.similar``.
        """
        params = clean_params({"include_similar": include_similar})
        return CompanyResponse.from_dict(
            self._client._get(f"/v1/companies/{domain_path(domain)}", params)
        )

    def reviews(
        self,
        domain: str,
        stars: Stars = None,
        language: str = "all",
        since: DateLike = None,
        until: DateLike = None,
        verified: bool = False,
        with_reply: bool = False,
        search: str | None = None,
        sort: ReviewSort = "recent",
        limit: int = 20,
        cursor: str | None = None,
    ) -> ReviewsResponse:
        """One page of reviews. Cost: 1 credit per 5 reviews returned (min 1).

        Args:
            domain: Company domain or URL.
            stars: Ratings to keep, e.g. ``[1, 2]`` or ``"1,2"``. All by default.
            language: ``"all"`` or an ISO 639-1 code (``"en"``, ``"it"``...).
            since: Published on/after (``date`` or ``YYYY-MM-DD`` / ISO 8601 string).
            until: Published on/before.
            verified: Only verified reviews.
            with_reply: Only reviews the company replied to.
            search: Full-text filter (max 100 chars).
            sort: ``"recent"`` or ``"relevant"``.
            limit: Reviews per page, 1-100. Lowered by the API if the balance cannot pay it.
            cursor: ``meta.next_cursor`` of the previous page (same filters).
        """
        params = _review_params(
            stars, language, since, until, verified, with_reply, search, sort, limit, cursor
        )
        return ReviewsResponse.from_dict(
            self._client._get(f"/v1/companies/{domain_path(domain)}/reviews", params)
        )

    def iter_reviews(
        self,
        domain: str,
        stars: Stars = None,
        language: str = "all",
        since: DateLike = None,
        until: DateLike = None,
        verified: bool = False,
        with_reply: bool = False,
        search: str | None = None,
        sort: ReviewSort = "recent",
        page_size: int = 100,
        max_reviews: int | None = None,
    ) -> Iterator[Review]:
        """Iterate over reviews, following ``meta.next_cursor`` page by page.

        Same filters as :meth:`reviews`. Every page is billed as it is fetched; stop early
        (``break`` or ``max_reviews``) to spend less.
        """
        cursor: str | None = None
        yielded = 0
        while True:
            limit = _page_limit(page_size, max_reviews, yielded)
            if limit == 0:
                return
            page = self.reviews(
                domain,
                stars,
                language,
                since,
                until,
                verified,
                with_reply,
                search,
                sort,
                limit,
                cursor,
            )
            yield from page.data
            yielded += len(page.data)
            cursor = page.meta.next_cursor
            if not cursor:
                return


class AsyncCompaniesAPI:
    """Async ``client.companies``."""

    def __init__(self, client: AsyncScrapeReviews):
        self._client = client

    async def search(
        self, query: str, limit: int = 10, cursor: str | None = None
    ) -> SearchResponse:
        """Search Trustpilot companies by name or domain. See :meth:`CompaniesAPI.search`."""
        params = clean_params({"query": query, "limit": limit, "cursor": cursor})
        return SearchResponse.from_dict(await self._client._get("/v1/companies/search", params))

    async def get(self, domain: str, include_similar: bool = False) -> CompanyResponse:
        """Full company profile. See :meth:`CompaniesAPI.get`."""
        params = clean_params({"include_similar": include_similar})
        return CompanyResponse.from_dict(
            await self._client._get(f"/v1/companies/{domain_path(domain)}", params)
        )

    async def reviews(
        self,
        domain: str,
        stars: Stars = None,
        language: str = "all",
        since: DateLike = None,
        until: DateLike = None,
        verified: bool = False,
        with_reply: bool = False,
        search: str | None = None,
        sort: ReviewSort = "recent",
        limit: int = 20,
        cursor: str | None = None,
    ) -> ReviewsResponse:
        """One page of reviews. See :meth:`CompaniesAPI.reviews`."""
        params = _review_params(
            stars, language, since, until, verified, with_reply, search, sort, limit, cursor
        )
        return ReviewsResponse.from_dict(
            await self._client._get(f"/v1/companies/{domain_path(domain)}/reviews", params)
        )

    async def iter_reviews(
        self,
        domain: str,
        stars: Stars = None,
        language: str = "all",
        since: DateLike = None,
        until: DateLike = None,
        verified: bool = False,
        with_reply: bool = False,
        search: str | None = None,
        sort: ReviewSort = "recent",
        page_size: int = 100,
        max_reviews: int | None = None,
    ) -> AsyncIterator[Review]:
        """Async iterate over reviews. See :meth:`CompaniesAPI.iter_reviews`."""
        cursor: str | None = None
        yielded = 0
        while True:
            limit = _page_limit(page_size, max_reviews, yielded)
            if limit == 0:
                return
            page = await self.reviews(
                domain,
                stars,
                language,
                since,
                until,
                verified,
                with_reply,
                search,
                sort,
                limit,
                cursor,
            )
            for review in page.data:
                yield review
            yielded += len(page.data)
            cursor = page.meta.next_cursor
            if not cursor:
                return


def _review_params(
    stars: Stars,
    language: str,
    since: DateLike,
    until: DateLike,
    verified: bool,
    with_reply: bool,
    search: str | None,
    sort: str,
    limit: int,
    cursor: str | None,
) -> dict[str, Any]:
    if stars is not None and not isinstance(stars, str):
        stars = list(stars)
    return clean_params(
        {
            "stars": stars or None,
            "language": None if language == "all" else language,
            "since": since,
            "until": until,
            "verified": verified,
            "with_reply": with_reply,
            "search": search,
            "sort": sort,
            "limit": limit,
            "cursor": cursor,
        }
    )


def _page_limit(page_size: int, max_reviews: int | None, yielded: int) -> int:
    if max_reviews is None:
        return page_size
    return max(0, min(page_size, max_reviews - yielded))
