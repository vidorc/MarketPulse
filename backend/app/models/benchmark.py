"""Ground-truth labels and benchmark results (Phase 3)."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import LabelSource


class GroundTruth(Base, TimestampMixin):
    __tablename__ = "ground_truth"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Either linked to an ingested article, or matched by title for seed labels.
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(Text, index=True)
    # Comma-separated canonical NSE tickers, e.g. "ADANIPORTS,TCS".
    expected_tickers: Mapped[str] = mapped_column(Text, default="")
    expected_type: Mapped[str | None] = mapped_column(String(48), nullable=True)
    label_source: Mapped[str] = mapped_column(String(16), default=LabelSource.seed.value)
    labeled_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )


class BenchmarkResult(Base, TimestampMixin):
    __tablename__ = "benchmark_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    processing_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("processing_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # "overall" or "per_category"; category set only for per-category rows.
    scope: Mapped[str] = mapped_column(String(16), default="overall")
    category: Mapped[str | None] = mapped_column(String(48), nullable=True)
    precision: Mapped[float] = mapped_column(Float, default=0.0)
    recall: Mapped[float] = mapped_column(Float, default=0.0)
    f1: Mapped[float] = mapped_column(Float, default=0.0)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    tp: Mapped[int] = mapped_column(Integer, default=0)
    fp: Mapped[int] = mapped_column(Integer, default=0)
    fn: Mapped[int] = mapped_column(Integer, default=0)
