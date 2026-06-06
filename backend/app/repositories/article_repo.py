"""Article repository — persistence and queries for articles and their outputs."""
from __future__ import annotations

import hashlib

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.article import (
    Article,
    ArticleCompany,
    Classification,
    Sentiment,
)
from app.models.enums import ArticleStatus


def compute_content_hash(title: str, body: str) -> str:
    norm = f"{(title or '').strip().lower()}|{(body or '').strip().lower()}"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


class ArticleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_hash(self, content_hash: str) -> Article | None:
        return self.db.execute(
            select(Article).where(Article.content_hash == content_hash)
        ).scalar_one_or_none()

    def get(self, article_id: int) -> Article | None:
        return self.db.execute(
            select(Article)
            .where(Article.id == article_id)
            .options(
                selectinload(Article.classification),
                selectinload(Article.article_companies).selectinload(ArticleCompany.company),
                selectinload(Article.article_companies).selectinload(ArticleCompany.ticker),
                selectinload(Article.sentiments).selectinload(Sentiment.company),
            )
        ).scalar_one_or_none()

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        article_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Article], int]:
        stmt = select(Article).options(
            selectinload(Article.classification),
            selectinload(Article.article_companies).selectinload(ArticleCompany.ticker),
        )
        count_stmt = select(func.count(Article.id))

        if article_type:
            stmt = stmt.join(Classification).where(
                Classification.article_type == article_type
            )
            count_stmt = count_stmt.join(Classification).where(
                Classification.article_type == article_type
            )
        if status:
            stmt = stmt.where(Article.status == status)
            count_stmt = count_stmt.where(Article.status == status)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(Article.title.ilike(like))
            count_stmt = count_stmt.where(Article.title.ilike(like))

        total = self.db.execute(count_stmt).scalar_one()
        rows = (
            self.db.execute(
                stmt.order_by(Article.created_at.desc()).limit(limit).offset(offset)
            )
            .scalars()
            .all()
        )
        return list(rows), total

    def create(
        self,
        *,
        title: str,
        body: str,
        content_hash: str,
        url: str | None = None,
        source: str | None = None,
        processing_run_id: int | None = None,
    ) -> Article:
        article = Article(
            title=title,
            body=body,
            content_hash=content_hash,
            url=url,
            source=source,
            processing_run_id=processing_run_id,
            status=ArticleStatus.pending.value,
        )
        self.db.add(article)
        self.db.flush()
        return article
