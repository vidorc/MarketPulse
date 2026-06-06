"""Pydantic schemas for article-related API responses and requests."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompanyMention(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company_id: int
    company_name: str
    ticker: str | None = None
    alias_used: str | None = None
    confidence: int = 0
    sentiment: str | None = None
    is_manual_correction: bool = False


class ClassificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    article_type: str
    impact: str
    confidence: int
    reasoning: str
    raw_llm_json: str = ""


class ArticleSummary(BaseModel):
    """Compact shape for list/feed views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source: str | None = None
    url: str | None = None
    status: str
    article_type: str | None = None
    confidence: int | None = None
    impact: str | None = None
    tickers: list[str] = []
    created_at: datetime


class ArticleDetail(BaseModel):
    """Full article review payload."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    source: str | None = None
    url: str | None = None
    status: str
    created_at: datetime
    classification: ClassificationOut | None = None
    companies: list[CompanyMention] = []


class ArticleListResponse(BaseModel):
    items: list[ArticleSummary]
    total: int
    limit: int
    offset: int


# --- Ingestion ---


class CsvValidationResponse(BaseModel):
    valid: bool
    total_rows: int
    valid_rows: int
    columns: list[str]
    issues: list[str]
    preview: list[dict]
    run_id: int | None = None  # set once an upload is staged for processing


class ProcessRequest(BaseModel):
    run_id: int
    async_mode: bool = False  # dispatch to Celery instead of processing inline


class ProcessRunResponse(BaseModel):
    run_id: int
    status: str
    total_rows: int
    processed: int
    failed: int


# --- Manual correction (Phase 1 surface; enforced by RBAC in Phase 2) ---


class CorrectionRequest(BaseModel):
    tickers: list[str]
    article_type: str | None = None
