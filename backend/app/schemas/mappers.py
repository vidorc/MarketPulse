"""Mappers from ORM models to API schemas.

Keeping this conversion in one place stops endpoints from reaching into ORM
internals and keeps the response shapes consistent across routes.
"""
from __future__ import annotations

from app.models.article import Article
from app.schemas.article import (
    ArticleDetail,
    ArticleSummary,
    ClassificationOut,
    CompanyMention,
)


def article_to_summary(article: Article) -> ArticleSummary:
    cls = article.classification
    tickers = [
        ac.ticker.symbol for ac in article.article_companies if ac.ticker is not None
    ]
    return ArticleSummary(
        id=article.id,
        title=article.title,
        source=article.source,
        url=article.url,
        status=article.status,
        article_type=cls.article_type if cls else None,
        confidence=cls.confidence if cls else None,
        impact=cls.impact if cls else None,
        tickers=tickers,
        created_at=article.created_at,
    )


def article_to_detail(article: Article) -> ArticleDetail:
    cls = article.classification
    sentiment_by_company = {s.company_id: s.label for s in article.sentiments}

    companies = [
        CompanyMention(
            company_id=ac.company_id,
            company_name=ac.company.canonical_name,
            ticker=ac.ticker.symbol if ac.ticker else None,
            alias_used=ac.alias_used,
            confidence=ac.confidence,
            sentiment=sentiment_by_company.get(ac.company_id),
            is_manual_correction=ac.is_manual_correction,
        )
        for ac in article.article_companies
    ]

    return ArticleDetail(
        id=article.id,
        title=article.title,
        body=article.body,
        source=article.source,
        url=article.url,
        status=article.status,
        created_at=article.created_at,
        classification=ClassificationOut.model_validate(cls) if cls else None,
        companies=companies,
    )
