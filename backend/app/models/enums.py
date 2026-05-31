"""Shared domain enumerations (stored as strings for DB portability)."""
from enum import StrEnum


class ArticleType(StrEnum):
    company_specific = "company_specific"
    market_movers = "market_movers"
    broker_recommendations = "broker_recommendations"
    technical_analysis = "technical_analysis"
    macro_or_sector = "macro_or_sector"
    earnings = "earnings"
    mergers_and_acquisitions = "mergers_and_acquisitions"
    regulatory = "regulatory"
    management_commentary = "management_commentary"


# Legacy / model-emitted types normalized onto the canonical set above.
ARTICLE_TYPE_ALIASES: dict[str, ArticleType] = {
    "multi_company_news": ArticleType.market_movers,
    "company": ArticleType.company_specific,
    "macro": ArticleType.macro_or_sector,
    "sector": ArticleType.macro_or_sector,
    "broker": ArticleType.broker_recommendations,
    "technical": ArticleType.technical_analysis,
    "m_and_a": ArticleType.mergers_and_acquisitions,
    "ma": ArticleType.mergers_and_acquisitions,
}


def normalize_article_type(raw: str | None) -> ArticleType:
    """Map an arbitrary model/legacy string onto a canonical ArticleType.

    Falls back to ``macro_or_sector`` for unknown/empty values (the most neutral
    bucket, used for broad-market pieces with no named companies)."""
    if not raw:
        return ArticleType.macro_or_sector
    key = raw.strip().lower()
    try:
        return ArticleType(key)
    except ValueError:
        return ARTICLE_TYPE_ALIASES.get(key, ArticleType.macro_or_sector)


class Sentiment(StrEnum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


def normalize_sentiment(raw: str | None) -> Sentiment:
    if not raw:
        return Sentiment.neutral
    key = raw.strip().lower()
    try:
        return Sentiment(key)
    except ValueError:
        return Sentiment.neutral


class Impact(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


def normalize_impact(raw: str | None) -> Impact:
    if not raw:
        return Impact.low
    key = raw.strip().lower()
    if key in ("med", "mid", "moderate"):
        return Impact.medium
    try:
        return Impact(key)
    except ValueError:
        return Impact.low


class UserRole(StrEnum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class ProcessingStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class ArticleStatus(StrEnum):
    pending = "pending"
    processed = "processed"
    failed = "failed"


class AliasSource(StrEnum):
    generated = "generated"
    acronym = "acronym"
    manual = "manual"


class LabelSource(StrEnum):
    seed = "seed"
    analyst = "analyst"
