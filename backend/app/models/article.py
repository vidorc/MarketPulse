"""Article and its per-article LLM output models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ArticleStatus


class Article(Base, TimestampMixin):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source: Mapped[str | None] = mapped_column(String(256), nullable=True)
    date_published: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Idempotency key: sha256 of normalized title+body. Unique => dedupe.
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default=ArticleStatus.pending.value)
    processing_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("processing_runs.id", ondelete="SET NULL"), nullable=True
    )

    processing_run: Mapped["ProcessingRun | None"] = relationship(
        "ProcessingRun", back_populates="articles"
    )
    classification: Mapped["Classification | None"] = relationship(
        "Classification", back_populates="article", uselist=False,
        cascade="all, delete-orphan",
    )
    article_companies: Mapped[list["ArticleCompany"]] = relationship(
        "ArticleCompany", back_populates="article", cascade="all, delete-orphan"
    )
    sentiments: Mapped[list["Sentiment"]] = relationship(
        "Sentiment", back_populates="article", cascade="all, delete-orphan"
    )


class Classification(Base, TimestampMixin):
    __tablename__ = "classifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), unique=True
    )
    article_type: Mapped[str] = mapped_column(String(48))
    impact: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    raw_llm_json: Mapped[str] = mapped_column(Text, default="")

    article: Mapped["Article"] = relationship("Article", back_populates="classification")


class ArticleCompany(Base, TimestampMixin):
    """M2M join carrying per-link evidence (alias used, confidence, manual flag)."""

    __tablename__ = "article_companies"
    __table_args__ = (
        UniqueConstraint("article_id", "company_id", name="uq_article_company"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    ticker_id: Mapped[int | None] = mapped_column(
        ForeignKey("tickers.id", ondelete="SET NULL"), nullable=True
    )
    alias_used: Mapped[str | None] = mapped_column(String(512), nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    is_manual_correction: Mapped[bool] = mapped_column(default=False)

    article: Mapped["Article"] = relationship("Article", back_populates="article_companies")
    company: Mapped["Company"] = relationship("Company")
    ticker: Mapped["Ticker | None"] = relationship("Ticker")


class Sentiment(Base, TimestampMixin):
    __tablename__ = "sentiments"
    __table_args__ = (
        UniqueConstraint("article_id", "company_id", name="uq_article_company_sentiment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(16))
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    article: Mapped["Article"] = relationship("Article", back_populates="sentiments")
    company: Mapped["Company"] = relationship("Company")
