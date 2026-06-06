"""Processing pipeline.

Orchestrates the core loop for a single article:
    extract (LLM) -> resolve companies -> persist classification/links/sentiment
    -> emit audit event.

Idempotent via the article content hash: re-processing the same article returns the
existing record instead of duplicating work.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.article import (
    Article,
    ArticleCompany,
    Classification,
    Sentiment,
)
from app.models.enums import (
    ArticleStatus,
    normalize_article_type,
    normalize_impact,
    normalize_sentiment,
)
from app.repositories.article_repo import ArticleRepository, compute_content_hash
from app.repositories.audit_repo import AuditRepository
from app.services.llm.base import LLMProvider
from app.services.resolution.service import ResolutionService

logger = get_logger("app.services.pipeline")


@dataclass
class PipelineOutcome:
    article: Article
    created: bool
    resolved_tickers: list[str]
    alias_misses: list[str]


class PipelineService:
    def __init__(
        self,
        db: Session,
        llm: LLMProvider,
        resolution: ResolutionService,
    ) -> None:
        self.db = db
        self.llm = llm
        self.resolution = resolution
        self.articles = ArticleRepository(db)
        self.audit = AuditRepository(db)

    def process_article(
        self,
        *,
        title: str,
        body: str = "",
        url: str | None = None,
        source: str | None = None,
        processing_run_id: int | None = None,
    ) -> PipelineOutcome:
        title = (title or "").strip()
        if not title:
            raise ValueError("Article title is required.")

        content_hash = compute_content_hash(title, body)
        existing = self.articles.get_by_hash(content_hash)
        if existing is not None:
            logger.info("Skipping duplicate article (hash hit): %s", title[:60])
            tickers = [
                ac.ticker.symbol
                for ac in existing.article_companies
                if ac.ticker is not None
            ]
            return PipelineOutcome(
                article=existing, created=False, resolved_tickers=tickers, alias_misses=[]
            )

        article = self.articles.create(
            title=title,
            body=body,
            content_hash=content_hash,
            url=url,
            source=source,
            processing_run_id=processing_run_id,
        )

        # 1. LLM extraction.
        result = self.llm.extract(title, body)

        # 2. Persist classification.
        classification = Classification(
            article_id=article.id,
            article_type=normalize_article_type(result.article_type).value,
            impact=normalize_impact(result.impact).value,
            confidence=result.confidence,
            reasoning=result.reasoning,
            raw_llm_json=result.raw_json,
        )
        self.db.add(classification)

        # 3. Resolve companies -> tickers, persist links + per-company sentiment.
        #    Resolve each extraction inline so its name+sentiment stay attached to
        #    the resolved company. De-dup by company_id (first mention wins).
        resolved_tickers: list[str] = []
        alias_misses: list[str] = []
        seen_company_ids: set[int] = set()

        for extraction in result.companies:
            hit = self.resolution.resolve(extraction.name)
            if hit is None:
                alias_misses.append(extraction.name)
                continue
            if hit.company_id in seen_company_ids:
                continue
            seen_company_ids.add(hit.company_id)

            self.db.add(
                ArticleCompany(
                    article_id=article.id,
                    company_id=hit.company_id,
                    ticker_id=hit.ticker_id,
                    alias_used=hit.alias_used,
                    confidence=result.confidence,
                )
            )
            self.db.add(
                Sentiment(
                    article_id=article.id,
                    company_id=hit.company_id,
                    label=normalize_sentiment(extraction.sentiment).value,
                )
            )
            if hit.ticker_symbol:
                resolved_tickers.append(hit.ticker_symbol)

        # 4. Finalize + audit.
        article.status = (
            ArticleStatus.processed.value
            if result.error is None
            else ArticleStatus.failed.value
        )
        self.audit.log(
            action="article_processed",
            entity_type="article",
            entity_id=article.id,
            after={
                "article_type": classification.article_type,
                "tickers": resolved_tickers,
                "alias_misses": alias_misses,
                "confidence": result.confidence,
            },
            message=result.reasoning[:500] if result.reasoning else None,
        )
        self.db.flush()

        return PipelineOutcome(
            article=article,
            created=True,
            resolved_tickers=resolved_tickers,
            alias_misses=alias_misses,
        )

