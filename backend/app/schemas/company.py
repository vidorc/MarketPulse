"""Pydantic schemas for company-related API responses."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AliasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alias_text: str
    source: str


class CompanySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_name: str
    ticker: str | None = None
    mention_count: int = 0


class MentionTimelineEntry(BaseModel):
    article_id: int
    title: str
    sentiment: str | None = None
    created_at: datetime


class SentimentTrendPoint(BaseModel):
    label: str  # positive | neutral | negative
    count: int


class CompanyDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_name: str
    ticker: str | None = None
    aliases: list[AliasOut] = []
    mention_count: int = 0
    recent_mentions: list[MentionTimelineEntry] = []
    sentiment_trend: list[SentimentTrendPoint] = []


class CompanyListResponse(BaseModel):
    items: list[CompanySummary]
    total: int
    limit: int
    offset: int
