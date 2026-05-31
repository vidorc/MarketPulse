"""ProcessingRun — one ingestion/processing batch (CSV upload run)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ProcessingStatus


class ProcessingRun(Base, TimestampMixin):
    __tablename__ = "processing_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Storage locator for the uploaded file (set before processing starts).
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default=ProcessingStatus.pending.value)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    articles: Mapped[list["Article"]] = relationship(
        "Article", back_populates="processing_run"
    )
