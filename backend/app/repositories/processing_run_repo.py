"""ProcessingRun repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.models.enums import ProcessingStatus
from app.models.processing_run import ProcessingRun


class ProcessingRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self, *, source_filename: str | None, storage_key: str | None, total_rows: int
    ) -> ProcessingRun:
        run = ProcessingRun(
            source_filename=source_filename,
            storage_key=storage_key,
            total_rows=total_rows,
            status=ProcessingStatus.pending.value,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def get(self, run_id: int) -> ProcessingRun | None:
        return self.db.get(ProcessingRun, run_id)

    def mark_running(self, run: ProcessingRun) -> None:
        run.status = ProcessingStatus.running.value
        run.started_at = utcnow()
        self.db.flush()

    def mark_finished(self, run: ProcessingRun, *, failed: bool = False) -> None:
        run.status = (
            ProcessingStatus.failed.value if failed else ProcessingStatus.completed.value
        )
        run.finished_at = utcnow()
        self.db.flush()

    def increment(self, run: ProcessingRun, *, processed: int = 0, failed: int = 0) -> None:
        run.processed += processed
        run.failed += failed
        self.db.flush()

    def list_recent(self, limit: int = 10) -> list[ProcessingRun]:
        return list(
            self.db.execute(
                select(ProcessingRun).order_by(ProcessingRun.created_at.desc()).limit(limit)
            ).scalars()
        )
