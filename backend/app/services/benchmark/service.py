"""Benchmark service — runs the metric engine against the DB.

Pulls each ground-truth label, finds the matching article (by explicit article_id
link, else by normalized title), collects that article's predicted tickers, scores
the pair with the pure engine, then persists overall + per-category
:class:`BenchmarkResult` rows. Read paths assemble the dashboard payloads
(latest metrics, per-category breakdown, FP/FN lists, trend history).
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.article import Article, ArticleCompany
from app.models.benchmark import BenchmarkResult
from app.repositories.benchmark_repo import (
    BenchmarkResultRepository,
    GroundTruthRepository,
    normalize_title,
)
from app.services.benchmark.engine import (
    BenchmarkReport,
    EvalItem,
    compute_benchmark,
    normalize_ticker_set,
)


@dataclass
class RunBenchmarkResult:
    evaluated: int
    matched_articles: int
    overall: BenchmarkResult
    per_category: list[BenchmarkResult]


def _predicted_tickers_by_article(db: Session) -> dict[int, set[str]]:
    """Map article_id -> set of predicted ticker symbols (from resolved links)."""
    stmt = (
        select(Article)
        .options(selectinload(Article.article_companies).selectinload(ArticleCompany.ticker))
    )
    out: dict[int, set[str]] = {}
    for article in db.execute(stmt).scalars():
        out[article.id] = {
            ac.ticker.symbol.upper()
            for ac in article.article_companies
            if ac.ticker and ac.ticker.symbol
        }
    return out


def _article_index(db: Session) -> dict[str, int]:
    """Normalized-title -> article_id, for matching seed labels to ingested
    articles when no explicit link exists. Last write wins; titles are expected
    to be effectively unique in the news set."""
    idx: dict[str, int] = {}
    for aid, title in db.execute(select(Article.id, Article.title)):
        idx[normalize_title(title)] = aid
    return idx


def build_eval_items(db: Session) -> list[EvalItem]:
    """Join ground truth to predictions, producing scorable items.

    A ground-truth label contributes an item only when its article is present in
    the DB (linked by id or matched by title) — we can't score predictions for an
    article that was never ingested."""
    gts = GroundTruthRepository(db).all()
    preds = _predicted_tickers_by_article(db)
    title_idx = _article_index(db)

    items: list[EvalItem] = []
    for gt in gts:
        article_id = gt.article_id
        if article_id is None:
            article_id = title_idx.get(normalize_title(gt.title))
        if article_id is None or article_id not in preds:
            continue  # no matching ingested article to score against
        items.append(
            EvalItem(
                title=gt.title,
                predicted=preds[article_id],
                expected=normalize_ticker_set(gt.expected_tickers),
                category=gt.expected_type,
                article_id=article_id,
            )
        )
    return items


def _to_rows(report: BenchmarkReport, run_id: int | None) -> tuple[BenchmarkResult, list[BenchmarkResult]]:
    overall = BenchmarkResult(
        processing_run_id=run_id,
        scope="overall",
        category=None,
        precision=report.overall.precision,
        recall=report.overall.recall,
        f1=report.overall.f1,
        accuracy=report.overall.accuracy,
        tp=report.overall.tp,
        fp=report.overall.fp,
        fn=report.overall.fn,
    )
    per_cat = [
        BenchmarkResult(
            processing_run_id=run_id,
            scope="per_category",
            category=m.category,
            precision=m.counts.precision,
            recall=m.counts.recall,
            f1=m.counts.f1,
            accuracy=m.counts.accuracy,
            tp=m.counts.tp,
            fp=m.counts.fp,
            fn=m.counts.fn,
        )
        for m in report.per_category
    ]
    return overall, per_cat


def run_benchmark(db: Session, *, processing_run_id: int | None = None) -> RunBenchmarkResult:
    """Compute and persist benchmark results. Replaces any prior results scoped to
    the same run so 'latest' stays unambiguous. Caller commits."""
    items = build_eval_items(db)
    report = compute_benchmark(items)

    repo = BenchmarkResultRepository(db)
    repo.clear_for_run(processing_run_id)
    overall_row, per_cat_rows = _to_rows(report, processing_run_id)
    repo.add(overall_row)
    for row in per_cat_rows:
        repo.add(row)

    return RunBenchmarkResult(
        evaluated=report.evaluated,
        matched_articles=report.evaluated,
        overall=overall_row,
        per_category=per_cat_rows,
    )


def latest_report(db: Session) -> BenchmarkReport | None:
    """Recompute the live report from current articles + ground truth for the
    FP/FN lists and per-category breakdown the dashboards render. Returns None when
    there is nothing to score yet."""
    items = build_eval_items(db)
    if not items:
        return None
    return compute_benchmark(items)
