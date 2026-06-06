"""Company repository — queries for the Company Explorer and analytics."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.alias import Alias
from app.models.article import Article, ArticleCompany, Sentiment
from app.models.company import Company, Ticker


class CompanyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, company_id: int) -> Company | None:
        return self.db.execute(
            select(Company)
            .where(Company.id == company_id)
            .options(
                selectinload(Company.aliases),
                selectinload(Company.primary_ticker),
            )
        ).scalar_one_or_none()

    def mention_count(self, company_id: int) -> int:
        return self.db.execute(
            select(func.count(ArticleCompany.id)).where(
                ArticleCompany.company_id == company_id
            )
        ).scalar_one()

    def recent_mentions(self, company_id: int, limit: int = 10):
        """Return recent (article, sentiment_label) tuples for a company."""
        stmt = (
            select(Article, Sentiment.label)
            .join(ArticleCompany, ArticleCompany.article_id == Article.id)
            .join(
                Sentiment,
                (Sentiment.article_id == Article.id)
                & (Sentiment.company_id == company_id),
                isouter=True,
            )
            .where(ArticleCompany.company_id == company_id)
            .order_by(Article.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).all())

    def sentiment_trend(self, company_id: int) -> list[tuple[str, int]]:
        stmt = (
            select(Sentiment.label, func.count(Sentiment.id))
            .where(Sentiment.company_id == company_id)
            .group_by(Sentiment.label)
        )
        return list(self.db.execute(stmt).all())

    def list_with_mentions(
        self, *, limit: int = 50, offset: int = 0, search: str | None = None
    ) -> tuple[list[tuple[Company, str | None, int]], int]:
        """List companies with their ticker and mention count.

        Only companies that have at least one mention are returned by default
        ordering (most-mentioned first), but the full list is searchable.
        """
        mention_sq = (
            select(
                ArticleCompany.company_id.label("cid"),
                func.count(ArticleCompany.id).label("mentions"),
            )
            .group_by(ArticleCompany.company_id)
            .subquery()
        )

        stmt = (
            select(
                Company,
                Ticker.symbol,
                func.coalesce(mention_sq.c.mentions, 0).label("mentions"),
            )
            .join(Ticker, Company.primary_ticker_id == Ticker.id, isouter=True)
            .join(mention_sq, mention_sq.c.cid == Company.id, isouter=True)
        )
        count_stmt = select(func.count(Company.id))

        if search:
            like = f"%{search}%"
            stmt = stmt.where(Company.canonical_name.ilike(like))
            count_stmt = count_stmt.where(Company.canonical_name.ilike(like))

        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(func.coalesce(mention_sq.c.mentions, 0).desc()).limit(
            limit
        ).offset(offset)
        rows = [(c, sym, mentions) for c, sym, mentions in self.db.execute(stmt).all()]
        return rows, total
