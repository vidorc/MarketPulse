"""Run orchestration — processes a batch of CSV rows under a ProcessingRun.

Used by both the synchronous upload path (small files) and the Celery task (large
files). Per-row failures are recorded against the run and never abort the batch.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.enums import ArticleStatus
from app.models.processing_run import ProcessingRun
from app.repositories.processing_run_repo import ProcessingRunRepository
from app.services.llm.factory import get_llm_provider
from app.services.pipeline.ingestion import CsvRow
from app.services.pipeline.service import PipelineService
from app.services.resolution.service import ResolutionService

logger = get_logger("app.services.pipeline.run")


def create_run(
    db: Session, *, source_filename: str | None, storage_key: str | None, total_rows: int
) -> ProcessingRun:
    repo = ProcessingRunRepository(db)
    run = repo.create(
        source_filename=source_filename, storage_key=storage_key, total_rows=total_rows
    )
    db.commit()
    return run


def process_rows(
    db: Session,
    run_id: int,
    rows: list[CsvRow],
    *,
    pipeline: PipelineService | None = None,
) -> ProcessingRun:
    """Process every row under ``run_id``.

    Commits incrementally per row so a crash mid-batch leaves completed rows
    persisted. Counters are reset at the start so a re-run (e.g. a Celery retry)
    does not double-count. The run always reaches a terminal state: if building
    the pipeline fails, the run is marked ``failed`` before the error propagates.
    """
    repo = ProcessingRunRepository(db)
    run = repo.get(run_id)
    if run is None:
        raise ValueError(f"ProcessingRun {run_id} not found.")

    # Build the pipeline lazily; a provider-init failure must still drive the run
    # to a terminal state rather than leaving it stuck 'pending'/'running'.
    if pipeline is None:
        try:
            pipeline = PipelineService(db, get_llm_provider(), ResolutionService(db))
        except Exception:
            db.rollback()
            run = repo.get(run_id)
            if run is not None:
                repo.mark_finished(run, failed=True)
                db.commit()
            logger.exception("Failed to initialize pipeline for run %s", run_id)
            raise

    # Reset counters for idempotent re-runs, then mark running.
    run.processed = 0
    run.failed = 0
    repo.mark_running(run)
    db.commit()

    for row in rows:
        try:
            outcome = pipeline.process_article(
                title=row.title,
                body=row.body,
                url=row.url,
                source=row.source,
                processing_run_id=run.id,
            )
            # An article whose extraction errored is marked failed by the pipeline;
            # count it as failed, not processed, so counters match article status.
            if outcome.article.status == ArticleStatus.failed.value:
                repo.increment(run, failed=1)
            else:
                repo.increment(run, processed=1)
            db.commit()
        except Exception:  # noqa: BLE001 — isolate per-row failures
            # Guard the recovery path itself: if rollback/increment throws (dropped
            # connection, etc.) we log and continue rather than aborting the batch.
            try:
                db.rollback()
                run = repo.get(run_id)
                repo.increment(run, failed=1)
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Recovery path failed for run %s", run_id)
            logger.exception("Row failed in run %s: %s", run_id, row.title[:60])

    run = repo.get(run_id)
    # 'failed' status is reserved for a run that accomplished nothing; partial
    # failures are honestly reflected in the failed counter while status stays
    # 'completed' (the run did finish).
    repo.mark_finished(run, failed=run.processed == 0 and run.failed > 0)
    db.commit()
    logger.info(
        "Run %s finished: processed=%d failed=%d", run_id, run.processed, run.failed
    )
    return run
