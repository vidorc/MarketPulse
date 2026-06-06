"""Repositories for ground-truth labels and persisted benchmark results."""
from __future__ import annotations

from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session

from app.models.benchmark import BenchmarkResult, GroundTruth


def normalize_title(title: str) -> str:
    """Collapse whitespace + lowercase for matching ground truth to articles by
    title when no explicit article_id link exists."""
    return " ".join(str(title or "").split()).strip().lower()


class GroundTruthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_title(self, title: str) -> GroundTruth | None:
        stmt = select(GroundTruth).where(GroundTruth.title == title)
        return self.db.execute(stmt).scalars().first()

    def list(self, *, limit: int = 100, offset: int = 0) -> tuple[list[GroundTruth], int]:
        total = self.db.execute(select(func.count(GroundTruth.id))).scalar_one()
        rows = (
            self.db.execute(
                select(GroundTruth)
                .order_by(GroundTruth.id.asc())
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )
        return list(rows), total

    def all(self) -> list[GroundTruth]:
        return list(self.db.execute(select(GroundTruth)).scalars())

    def count(self) -> int:
        return self.db.execute(select(func.count(GroundTruth.id))).scalar_one()

    def create(
        self,
        *,
        title: str,
        expected_tickers: str,
        expected_type: str | None = None,
        label_source: str = "analyst",
        labeled_by: int | None = None,
        article_id: int | None = None,
    ) -> GroundTruth:
        gt = GroundTruth(
            title=title,
            expected_tickers=expected_tickers,
            expected_type=expected_type,
            label_source=label_source,
            labeled_by=labeled_by,
            article_id=article_id,
        )
        self.db.add(gt)
        self.db.flush()
        return gt


class BenchmarkResultRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, result: BenchmarkResult) -> BenchmarkResult:
        self.db.add(result)
        self.db.flush()
        return result

    def clear_for_run(self, processing_run_id: int | None) -> None:
        """Remove prior results for a run (or the global/null-run set) so a re-run
        replaces rather than appends, keeping 'latest' unambiguous."""
        self.db.execute(
            delete(BenchmarkResult).where(
                BenchmarkResult.processing_run_id.is_(processing_run_id)
                if processing_run_id is None
                else BenchmarkResult.processing_run_id == processing_run_id
            )
        )

    def latest_overall(self) -> BenchmarkResult | None:
        stmt = (
            select(BenchmarkResult)
            .where(BenchmarkResult.scope == "overall")
            .order_by(desc(BenchmarkResult.created_at), desc(BenchmarkResult.id))
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def for_run(self, processing_run_id: int | None) -> list[BenchmarkResult]:
        stmt = select(BenchmarkResult).where(
            BenchmarkResult.processing_run_id.is_(processing_run_id)
            if processing_run_id is None
            else BenchmarkResult.processing_run_id == processing_run_id
        )
        return list(self.db.execute(stmt).scalars())

    def overall_history(self, *, limit: int = 50) -> list[BenchmarkResult]:
        stmt = (
            select(BenchmarkResult)
            .where(BenchmarkResult.scope == "overall")
            .order_by(desc(BenchmarkResult.created_at), desc(BenchmarkResult.id))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars())
