"""Analytics aggregation service — powers the dashboard.

Computes headline totals and the distribution rollups the dashboard renders
(article-type mix, sentiment split, top-mentioned companies, daily processing
volume, confidence buckets) in SQL aggregates rather than pulling rows into
Python. Read-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.article import Article, ArticleCompany, Classification, Sentiment
from app.models.company import Company, Ticker
from app.models.enums import ArticleStatus
from app.models.processing_run import ProcessingRun


@dataclass
class LabelCount:
    label: str
    count: int


@dataclass
class TopCompany:
    company_id: int
    name: str
    ticker: str | None
    mentions: int


@dataclass
class AnalyticsOverview:
    total_articles: int
    processed_articles: int
    failed_articles: int
    total_companies: int
    companies_tagged: int  # companies with >= 1 mention
    avg_confidence: float
    total_runs: int
    article_types: list[LabelCount] = field(default_factory=list)
    sentiment_distribution: list[LabelCount] = field(default_factory=list)
    impact_distribution: list[LabelCount] = field(default_factory=list)
    top_companies: list[TopCompany] = field(default_factory=list)
    daily_volume: list[LabelCount] = field(default_factory=list)
    confidence_buckets: list[LabelCount] = field(default_factory=list)


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _scalar(self, stmt) -> int:
        return self.db.execute(stmt).scalar_one() or 0

    def _label_counts(self, stmt) -> list[LabelCount]:
        return [
            LabelCount(label=str(label), count=int(count))
            for label, count in self.db.execute(stmt).all()
            if label is not None
        ]

    def overview(self, *, top_n: int = 8, days: int = 14) -> AnalyticsOverview:
        total_articles = self._scalar(select(func.count(Article.id)))
        processed = self._scalar(
            select(func.count(Article.id)).where(
                Article.status == ArticleStatus.processed.value
            )
        )
        failed = self._scalar(
            select(func.count(Article.id)).where(
                Article.status == ArticleStatus.failed.value
            )
        )
        total_companies = self._scalar(select(func.count(Company.id)))
        companies_tagged = self._scalar(
            select(func.count(func.distinct(ArticleCompany.company_id)))
        )
        total_runs = self._scalar(select(func.count(ProcessingRun.id)))

        avg_conf = self.db.execute(
            select(func.avg(Classification.confidence))
        ).scalar_one()
        avg_confidence = round(float(avg_conf), 1) if avg_conf is not None else 0.0

        article_types = self._label_counts(
            select(Classification.article_type, func.count(Classification.id))
            .group_by(Classification.article_type)
            .order_by(func.count(Classification.id).desc())
        )
        sentiment_distribution = self._label_counts(
            select(Sentiment.label, func.count(Sentiment.id))
            .group_by(Sentiment.label)
            .order_by(func.count(Sentiment.id).desc())
        )
        impact_distribution = self._label_counts(
            select(Classification.impact, func.count(Classification.id))
            .group_by(Classification.impact)
            .order_by(func.count(Classification.id).desc())
        )

        top_companies = [
            TopCompany(
                company_id=cid, name=name, ticker=sym, mentions=int(mentions)
            )
            for cid, name, sym, mentions in self.db.execute(
                select(
                    Company.id,
                    Company.canonical_name,
                    Ticker.symbol,
                    func.count(ArticleCompany.id).label("mentions"),
                )
                .join(ArticleCompany, ArticleCompany.company_id == Company.id)
                .join(Ticker, Company.primary_ticker_id == Ticker.id, isouter=True)
                .group_by(Company.id, Company.canonical_name, Ticker.symbol)
                .order_by(func.count(ArticleCompany.id).desc())
                .limit(top_n)
            ).all()
        ]

        # Daily processing volume — group articles by calendar day. func.date works
        # on both SQLite and Postgres for a timestamp column.
        daily_volume = [
            LabelCount(label=str(day), count=int(count))
            for day, count in self.db.execute(
                select(func.date(Article.created_at), func.count(Article.id))
                .group_by(func.date(Article.created_at))
                .order_by(func.date(Article.created_at).desc())
                .limit(days)
            ).all()
            if day is not None
        ]
        daily_volume.reverse()  # oldest-first for a left-to-right chart

        confidence_buckets = self._confidence_buckets()

        return AnalyticsOverview(
            total_articles=total_articles,
            processed_articles=processed,
            failed_articles=failed,
            total_companies=total_companies,
            companies_tagged=companies_tagged,
            avg_confidence=avg_confidence,
            total_runs=total_runs,
            article_types=article_types,
            sentiment_distribution=sentiment_distribution,
            impact_distribution=impact_distribution,
            top_companies=top_companies,
            daily_volume=daily_volume,
            confidence_buckets=confidence_buckets,
        )

    def _confidence_buckets(self) -> list[LabelCount]:
        """Bucket classification confidence into 0-20 … 80-100 bands."""
        bands = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]
        out: list[LabelCount] = []
        for lo, hi in bands:
            count = self._scalar(
                select(func.count(Classification.id)).where(
                    Classification.confidence >= lo, Classification.confidence < hi
                )
            )
            label = f"{lo}-{hi if hi <= 100 else 100}"
            out.append(LabelCount(label=label, count=count))
        return out
