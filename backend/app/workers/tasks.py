"""Celery task definitions."""
from __future__ import annotations

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.services.pipeline.ingestion import CsvRow
from app.services.pipeline.run_service import process_rows
from app.workers.celery_app import celery_app

logger = get_logger("app.workers.tasks")


@celery_app.task(name="process_run")
def process_run_task(run_id: int, rows: list[dict]) -> dict:
    """Process a run's rows in the background.

    ``rows`` is a list of plain dicts (JSON-serializable) reconstructed into
    CsvRow objects, since Celery serializes task args as JSON.
    """
    csv_rows = [
        CsvRow(
            title=r.get("title", ""),
            body=r.get("body", ""),
            url=r.get("url"),
            source=r.get("source"),
        )
        for r in rows
    ]
    db = SessionLocal()
    try:
        run = process_rows(db, run_id, csv_rows)
        return {
            "run_id": run.id,
            "processed": run.processed,
            "failed": run.failed,
            "status": run.status,
        }
    finally:
        db.close()
