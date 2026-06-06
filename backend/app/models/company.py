"""Company and Ticker models.

A company has one canonical name and one or more tickers; ``primary_ticker_id``
points at its main NSE symbol. The companies<->tickers FK pair is circular, so the
``primary_ticker`` FK is created with ``use_alter`` for migration ordering.
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    primary_ticker_id: Mapped[int | None] = mapped_column(
        ForeignKey("tickers.id", use_alter=True, name="fk_company_primary_ticker"),
        nullable=True,
        index=True,
    )

    primary_ticker: Mapped[Ticker | None] = relationship(
        "Ticker",
        foreign_keys=[primary_ticker_id],
        post_update=True,
    )
    tickers: Mapped[list[Ticker]] = relationship(
        "Ticker",
        back_populates="company",
        foreign_keys="Ticker.company_id",
        cascade="all, delete-orphan",
    )
    aliases: Mapped[list["Alias"]] = relationship(
        "Alias", back_populates="company", cascade="all, delete-orphan"
    )


class Ticker(Base, TimestampMixin):
    __tablename__ = "tickers"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    series: Mapped[str | None] = mapped_column(String(16), nullable=True)
    isin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    face_value: Mapped[str | None] = mapped_column(String(32), nullable=True)

    company: Mapped[Company] = relationship(
        "Company", back_populates="tickers", foreign_keys=[company_id]
    )
