"""Alias model — generated and curated short-forms that resolve to a company."""
from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import AliasSource


class Alias(Base, TimestampMixin):
    __tablename__ = "aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    alias_text: Mapped[str] = mapped_column(String(512))
    # Normalized form is the lookup key; unique so resolution is deterministic.
    normalized: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(16), default=AliasSource.generated.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company: Mapped["Company"] = relationship("Company", back_populates="aliases")
