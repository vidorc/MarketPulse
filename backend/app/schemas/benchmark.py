"""Pydantic schemas for benchmarking and ground-truth labeling."""
from __future__ import annotations

from pydantic import BaseModel, Field


class MetricBlock(BaseModel):
    precision: float
    recall: float
    f1: float
    accuracy: float
    tp: int
    fp: int
    fn: int


class CategoryMetricOut(MetricBlock):
    category: str
    rows: int


class FalseItemOut(BaseModel):
    title: str
    predicted: list[str]
    expected: list[str]
    article_id: int | None = None


class BenchmarkResponse(BaseModel):
    """Full dashboard payload: headline metrics, per-category breakdown, and the
    false-positive / false-negative drill-down lists."""

    evaluated: int
    overall: MetricBlock
    per_category: list[CategoryMetricOut]
    false_positives: list[FalseItemOut]
    false_negatives: list[FalseItemOut]


class BenchmarkTrendPoint(BaseModel):
    created_at: str
    precision: float
    recall: float
    f1: float
    accuracy: float


class RunBenchmarkResponse(BaseModel):
    evaluated: int
    matched_articles: int
    overall: MetricBlock


# --- Ground truth ---


class GroundTruthOut(BaseModel):
    id: int
    article_id: int | None = None
    title: str
    expected_tickers: str
    expected_type: str | None = None
    label_source: str

    model_config = {"from_attributes": True}


class GroundTruthListResponse(BaseModel):
    items: list[GroundTruthOut]
    total: int


class GroundTruthCreate(BaseModel):
    title: str = Field(min_length=1)
    expected_tickers: list[str] = Field(default_factory=list)
    expected_type: str | None = None
    article_id: int | None = None
