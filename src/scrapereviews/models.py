"""Typed response models.

Every model is a dataclass built from the API's JSON with ``from_dict``. Unknown fields are
ignored, so new API fields never break older SDK versions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

Json = dict[str, Any]


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------


@dataclass
class Meta:
    """Billing information of a response."""

    credits_used: int
    cache_hit: bool = False

    @classmethod
    def from_dict(cls, d: Json) -> Meta:
        return cls(credits_used=d.get("credits_used", 0), cache_hit=d.get("cache_hit", False))


@dataclass
class ListMeta(Meta):
    """Meta of a paginated list. Pass ``next_cursor`` as ``cursor`` to get the next page."""

    count: int = 0
    total: int | None = None
    has_more: bool = False
    next_cursor: str | None = None

    @classmethod
    def from_dict(cls, d: Json) -> ListMeta:
        return cls(
            credits_used=d.get("credits_used", 0),
            cache_hit=d.get("cache_hit", False),
            count=d.get("count", 0),
            total=d.get("total"),
            has_more=d.get("has_more", False),
            next_cursor=d.get("next_cursor"),
        )


@dataclass
class ReviewsMeta(ListMeta):
    """``complete`` is False when Trustpilot's per-filter cap hid some matching reviews."""

    complete: bool = True

    @classmethod
    def from_dict(cls, d: Json) -> ReviewsMeta:
        base = ListMeta.from_dict(d)
        return cls(**vars(base), complete=d.get("complete", True))


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------


@dataclass
class CategoryRef:
    id: str
    name: str
    is_primary: bool = False

    @classmethod
    def from_dict(cls, d: Json) -> CategoryRef:
        return cls(id=d["id"], name=d["name"], is_primary=d.get("is_primary", False))


@dataclass
class ContactInfo:
    """Public business contact details as published on the company profile."""

    website: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    zip_code: str | None = None
    country: str | None = None

    @classmethod
    def from_dict(cls, d: Json | None) -> ContactInfo:
        d = d or {}
        return cls(
            website=d.get("website"),
            email=d.get("email"),
            phone=d.get("phone"),
            address=d.get("address"),
            city=d.get("city"),
            zip_code=d.get("zip_code"),
            country=d.get("country"),
        )


@dataclass
class StarDistribution:
    one: int = 0
    two: int = 0
    three: int = 0
    four: int = 0
    five: int = 0

    @classmethod
    def from_dict(cls, d: Json | None) -> StarDistribution:
        d = d or {}
        return cls(**{k: d.get(k, 0) for k in ("one", "two", "three", "four", "five")})


@dataclass
class LanguageCount:
    language: str
    count: int

    @classmethod
    def from_dict(cls, d: Json) -> LanguageCount:
        return cls(language=d["language"], count=d.get("count", 0))


@dataclass
class ReplyBehavior:
    reply_rate: float | None = None
    average_days_to_reply: float | None = None
    negative_reviews_count: int | None = None
    negative_reviews_with_reply_count: int | None = None
    last_reply_to_negative_review_at: str | None = None

    @classmethod
    def from_dict(cls, d: Json | None) -> ReplyBehavior:
        d = d or {}
        return cls(
            reply_rate=d.get("reply_rate"),
            average_days_to_reply=d.get("average_days_to_reply"),
            negative_reviews_count=d.get("negative_reviews_count"),
            negative_reviews_with_reply_count=d.get("negative_reviews_with_reply_count"),
            last_reply_to_negative_review_at=d.get("last_reply_to_negative_review_at"),
        )


@dataclass
class CompanySummary:
    """A company as it appears in search results and category rankings."""

    id: str
    domain: str
    name: str
    trustpilot_url: str
    trust_score: float | None = None
    stars: float | None = None
    review_count: int = 0
    logo_url: str | None = None
    categories: list[CategoryRef] = field(default_factory=list)
    contact: ContactInfo = field(default_factory=ContactInfo)

    @classmethod
    def from_dict(cls, d: Json) -> CompanySummary:
        return cls(
            id=d["id"],
            domain=d["domain"],
            name=d["name"],
            trustpilot_url=d["trustpilot_url"],
            trust_score=d.get("trust_score"),
            stars=d.get("stars"),
            review_count=d.get("review_count", 0),
            logo_url=d.get("logo_url"),
            categories=[CategoryRef.from_dict(c) for c in d.get("categories") or []],
            contact=ContactInfo.from_dict(d.get("contact")),
        )


@dataclass
class Company:
    """Full company profile."""

    id: str
    domain: str
    name: str
    trustpilot_url: str
    website: str | None = None
    trust_score: float | None = None
    stars: float | None = None
    review_count: int = 0
    review_count_last_12_months: int | None = None
    star_distribution: StarDistribution = field(default_factory=StarDistribution)
    languages: list[LanguageCount] = field(default_factory=list)
    categories: list[CategoryRef] = field(default_factory=list)
    description: str | None = None
    country: str | None = None
    contact: ContactInfo = field(default_factory=ContactInfo)
    is_claimed: bool = False
    claimed_at: str | None = None
    is_closed: bool = False
    is_temporarily_closed: bool = False
    is_using_paid_features: bool | None = None
    reply_behavior: ReplyBehavior = field(default_factory=ReplyBehavior)
    verified: bool = False
    consumer_alert: str | None = None
    logo_url: str | None = None
    similar: list[CompanySummary] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Json) -> Company:
        return cls(
            id=d["id"],
            domain=d["domain"],
            name=d["name"],
            trustpilot_url=d["trustpilot_url"],
            website=d.get("website"),
            trust_score=d.get("trust_score"),
            stars=d.get("stars"),
            review_count=d.get("review_count", 0),
            review_count_last_12_months=d.get("review_count_last_12_months"),
            star_distribution=StarDistribution.from_dict(d.get("star_distribution")),
            languages=[LanguageCount.from_dict(x) for x in d.get("languages") or []],
            categories=[CategoryRef.from_dict(c) for c in d.get("categories") or []],
            description=d.get("description"),
            country=d.get("country"),
            contact=ContactInfo.from_dict(d.get("contact")),
            is_claimed=d.get("is_claimed", False),
            claimed_at=d.get("claimed_at"),
            is_closed=d.get("is_closed", False),
            is_temporarily_closed=d.get("is_temporarily_closed", False),
            is_using_paid_features=d.get("is_using_paid_features"),
            reply_behavior=ReplyBehavior.from_dict(d.get("reply_behavior")),
            verified=d.get("verified", False),
            consumer_alert=d.get("consumer_alert"),
            logo_url=d.get("logo_url"),
            similar=[CompanySummary.from_dict(s) for s in d.get("similar") or []],
        )


@dataclass
class CompanyRef:
    """The company a page of reviews belongs to."""

    id: str
    domain: str
    name: str
    trustpilot_url: str
    trust_score: float | None = None
    review_count: int = 0

    @classmethod
    def from_dict(cls, d: Json) -> CompanyRef:
        return cls(
            id=d["id"],
            domain=d["domain"],
            name=d["name"],
            trustpilot_url=d["trustpilot_url"],
            trust_score=d.get("trust_score"),
            review_count=d.get("review_count", 0),
        )


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------


@dataclass
class ReviewAuthor:
    """Pseudonymised author: ``id`` is stable across reviews; no name or avatar."""

    id: str
    country: str | None = None
    review_count: int | None = None
    is_verified: bool | None = None

    @classmethod
    def from_dict(cls, d: Json) -> ReviewAuthor:
        return cls(
            id=d["id"],
            country=d.get("country"),
            review_count=d.get("review_count"),
            is_verified=d.get("is_verified"),
        )


@dataclass
class ReviewReply:
    text: str
    published_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_dict(cls, d: Json) -> ReviewReply:
        return cls(
            text=d["text"], published_at=d.get("published_at"), updated_at=d.get("updated_at")
        )


@dataclass
class Review:
    id: str
    rating: int
    published_at: str
    author: ReviewAuthor
    url: str
    title: str | None = None
    text: str | None = None
    language: str | None = None
    experienced_at: str | None = None
    updated_at: str | None = None
    is_verified: bool = False
    verification_source: str | None = None
    source: str | None = None
    likes: int = 0
    reply: ReviewReply | None = None

    @classmethod
    def from_dict(cls, d: Json) -> Review:
        reply = d.get("reply")
        return cls(
            id=d["id"],
            rating=d["rating"],
            published_at=d["published_at"],
            author=ReviewAuthor.from_dict(d["author"]),
            url=d["url"],
            title=d.get("title"),
            text=d.get("text"),
            language=d.get("language"),
            experienced_at=d.get("experienced_at"),
            updated_at=d.get("updated_at"),
            is_verified=d.get("is_verified", False),
            verification_source=d.get("verification_source"),
            source=d.get("source"),
            likes=d.get("likes", 0),
            reply=ReviewReply.from_dict(reply) if reply else None,
        )


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@dataclass
class Category:
    id: str
    name: str
    subcategories: list[Category] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Json) -> Category:
        return cls(
            id=d["id"],
            name=d["name"],
            subcategories=[Category.from_dict(s) for s in d.get("subcategories") or []],
        )


@dataclass
class CategoryInfo:
    """The category and country a company ranking refers to."""

    id: str
    country: str
    name: str | None = None

    @classmethod
    def from_dict(cls, d: Json) -> CategoryInfo:
        return cls(id=d["id"], country=d["country"], name=d.get("name"))


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


@dataclass
class SearchResponse:
    data: list[CompanySummary]
    meta: ListMeta

    @classmethod
    def from_dict(cls, d: Json) -> SearchResponse:
        return cls(
            data=[CompanySummary.from_dict(c) for c in d.get("data") or []],
            meta=ListMeta.from_dict(d.get("meta") or {}),
        )


@dataclass
class CompanyResponse:
    data: Company
    meta: Meta

    @classmethod
    def from_dict(cls, d: Json) -> CompanyResponse:
        return cls(data=Company.from_dict(d["data"]), meta=Meta.from_dict(d.get("meta") or {}))


@dataclass
class ReviewsResponse:
    company: CompanyRef
    data: list[Review]
    meta: ReviewsMeta

    @classmethod
    def from_dict(cls, d: Json) -> ReviewsResponse:
        return cls(
            company=CompanyRef.from_dict(d["company"]),
            data=[Review.from_dict(r) for r in d.get("data") or []],
            meta=ReviewsMeta.from_dict(d.get("meta") or {}),
        )


@dataclass
class CategoriesResponse:
    data: list[Category]
    meta: Meta

    @classmethod
    def from_dict(cls, d: Json) -> CategoriesResponse:
        return cls(
            data=[Category.from_dict(c) for c in d.get("data") or []],
            meta=Meta.from_dict(d.get("meta") or {}),
        )


@dataclass
class CategoryCompaniesResponse:
    category: CategoryInfo
    data: list[CompanySummary]
    meta: ListMeta

    @classmethod
    def from_dict(cls, d: Json) -> CategoryCompaniesResponse:
        return cls(
            category=CategoryInfo.from_dict(d["category"]),
            data=[CompanySummary.from_dict(c) for c in d.get("data") or []],
            meta=ListMeta.from_dict(d.get("meta") or {}),
        )
