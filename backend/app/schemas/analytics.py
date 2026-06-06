"""Pydantic schemas for analytics dashboard and audit log feed."""
from __future__ import annotations

from pydantic import BaseModel


class LabelCountOut(BaseModel):
    label: str
    count: int


class TopCompanyOut(BaseModel):
    company_id: int
    name: str
    ticker: str | None = None
    mentions: int


class AnalyticsOverviewOut(BaseModel):
    total_articles: int
    processed_articles: int
    failed_articles: int
    total_companies: int
    companies_tagged: int
    avg_confidence: float
    total_runs: int
    article_types: list[LabelCountOut]
    sentiment_distribution: list[LabelCountOut]
    impact_distribution: list[LabelCountOut]
    top_companies: list[TopCompanyOut]
    daily_volume: list[LabelCountOut]
    confidence_buckets: list[LabelCountOut]


# --- Audit ---


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None = None
    entity_type: str
    entity_id: str | None = None
    action: str
    before: dict | None = None
    after: dict | None = None
    message: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class AuditListResponse(BaseModel):
    items: list[AuditLogOut]
    total: int
