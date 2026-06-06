"""Benchmark + ground-truth endpoints (Phase 3).

- GET  /benchmarks          — live dashboard payload (metrics, per-category, FP/FN)
- POST /benchmarks/run      — recompute and persist a benchmark snapshot (analyst)
- GET  /benchmarks/trend    — overall metric history across snapshots
- GET  /ground-truth        — list labels
- POST /ground-truth        — add an analyst label (analyst)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_analyst
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.benchmark_repo import (
    BenchmarkResultRepository,
    GroundTruthRepository,
)
from app.schemas.benchmark import (
    BenchmarkResponse,
    BenchmarkTrendPoint,
    CategoryMetricOut,
    FalseItemOut,
    GroundTruthCreate,
    GroundTruthListResponse,
    GroundTruthOut,
    MetricBlock,
    RunBenchmarkResponse,
)
from app.services.benchmark import service as benchmark_service
from app.services.benchmark.engine import Counts, normalize_ticker_set

router = APIRouter(tags=["benchmarks"])


def _metric_block(c: Counts) -> MetricBlock:
    return MetricBlock(
        precision=c.precision,
        recall=c.recall,
        f1=c.f1,
        accuracy=c.accuracy,
        tp=c.tp,
        fp=c.fp,
        fn=c.fn,
    )


@router.get("/benchmarks", response_model=BenchmarkResponse)
def get_benchmarks(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BenchmarkResponse:
    """Compute the live benchmark report from current articles + ground truth.

    Returns an all-zero/empty payload (not an error) when nothing is scorable yet,
    so the dashboard can render an honest 'no data' state."""
    report = benchmark_service.latest_report(db)
    if report is None:
        return BenchmarkResponse(
            evaluated=0,
            overall=_metric_block(Counts()),
            per_category=[],
            false_positives=[],
            false_negatives=[],
        )
    return BenchmarkResponse(
        evaluated=report.evaluated,
        overall=_metric_block(report.overall),
        per_category=[
            CategoryMetricOut(
                category=m.category,
                rows=m.rows,
                precision=m.counts.precision,
                recall=m.counts.recall,
                f1=m.counts.f1,
                accuracy=m.counts.accuracy,
                tp=m.counts.tp,
                fp=m.counts.fp,
                fn=m.counts.fn,
            )
            for m in report.per_category
        ],
        false_positives=[
            FalseItemOut(
                title=f.title,
                predicted=f.predicted,
                expected=f.expected,
                article_id=f.article_id,
            )
            for f in report.false_positives
        ],
        false_negatives=[
            FalseItemOut(
                title=f.title,
                predicted=f.predicted,
                expected=f.expected,
                article_id=f.article_id,
            )
            for f in report.false_negatives
        ],
    )


@router.post("/benchmarks/run", response_model=RunBenchmarkResponse)
def run_benchmark(
    processing_run_id: int | None = Query(default=None),
    user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
) -> RunBenchmarkResponse:
    """Recompute and persist a benchmark snapshot (for trend history)."""
    result = benchmark_service.run_benchmark(db, processing_run_id=processing_run_id)
    AuditRepository(db).log(
        action="benchmark.run",
        entity_type="benchmark",
        entity_id=processing_run_id,
        actor_id=user.id,
        after={
            "evaluated": result.evaluated,
            "f1": result.overall.f1,
            "precision": result.overall.precision,
            "recall": result.overall.recall,
        },
    )
    db.commit()
    return RunBenchmarkResponse(
        evaluated=result.evaluated,
        matched_articles=result.matched_articles,
        overall=_metric_block(
            Counts(tp=result.overall.tp, fp=result.overall.fp, fn=result.overall.fn)
        ),
    )


@router.get("/benchmarks/trend", response_model=list[BenchmarkTrendPoint])
def benchmark_trend(
    limit: int = Query(50, ge=1, le=200),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BenchmarkTrendPoint]:
    rows = BenchmarkResultRepository(db).overall_history(limit=limit)
    # Oldest-first so a line chart reads left-to-right.
    rows = list(reversed(rows))
    return [
        BenchmarkTrendPoint(
            created_at=r.created_at.isoformat(),
            precision=r.precision,
            recall=r.recall,
            f1=r.f1,
            accuracy=r.accuracy,
        )
        for r in rows
    ]


@router.get("/ground-truth", response_model=GroundTruthListResponse)
def list_ground_truth(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GroundTruthListResponse:
    rows, total = GroundTruthRepository(db).list(limit=limit, offset=offset)
    return GroundTruthListResponse(
        items=[GroundTruthOut.model_validate(r) for r in rows], total=total
    )


@router.post("/ground-truth", response_model=GroundTruthOut, status_code=201)
def create_ground_truth(
    payload: GroundTruthCreate,
    user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
) -> GroundTruthOut:
    repo = GroundTruthRepository(db)
    # Normalize the supplied tickers through the engine's parser for consistency.
    joined = ",".join(sorted(normalize_ticker_set(",".join(payload.expected_tickers))))
    gt = repo.create(
        title=payload.title,
        expected_tickers=joined,
        expected_type=payload.expected_type,
        label_source="analyst",
        labeled_by=user.id,
        article_id=payload.article_id,
    )
    AuditRepository(db).log(
        action="ground_truth.create",
        entity_type="ground_truth",
        entity_id=gt.id,
        actor_id=user.id,
        after={"title": gt.title, "expected_tickers": gt.expected_tickers},
    )
    db.commit()
    db.refresh(gt)
    return GroundTruthOut.model_validate(gt)
