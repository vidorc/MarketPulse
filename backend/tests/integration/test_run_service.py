"""Processing-run lifecycle: counters, terminal state, and failure isolation.

These tests pin down the contract the review flagged as broken:
- a row whose LLM extraction errored counts as *failed*, not *processed*;
- re-processing a run (e.g. a Celery retry) resets counters instead of double-counting;
- an unrecoverable error (provider init, escaped exception) still drives the run to a
  terminal state rather than leaving it stuck 'running'.
"""
from __future__ import annotations

import pytest

from app.models.enums import ArticleStatus, ProcessingStatus
from app.repositories.processing_run_repo import ProcessingRunRepository
from app.services.llm.base import CompanyExtraction, ExtractionResult, LLMProvider
from app.services.pipeline import run_service
from app.services.pipeline.ingestion import CsvRow
from app.services.pipeline.service import PipelineService
from app.services.resolution.service import ResolutionService


class _SuccessProvider(LLMProvider):
    """Always returns a clean macro extraction (no companies → no resolution needed)."""

    name = "success"

    def extract(self, title: str, body: str) -> ExtractionResult:
        return ExtractionResult(
            article_type="macro_or_sector",
            companies=[],
            confidence=70,
            reasoning="ok",
            impact="low",
        )


class _ErrorProvider(LLMProvider):
    """Always returns an error result (e.g. exhausted Groq retries)."""

    name = "error"

    def extract(self, title: str, body: str) -> ExtractionResult:
        return ExtractionResult.empty_error("LLM unavailable")


def _rows(n: int) -> list[CsvRow]:
    return [CsvRow(title=f"Headline {i}", body=f"body {i}", url=None, source=None) for i in range(n)]


def _make_run(db, total: int):
    run = run_service.create_run(db, source_filename="t.csv", storage_key=None, total_rows=total)
    return run


def _pipeline(db, provider) -> PipelineService:
    return PipelineService(db, provider, ResolutionService(db))


class TestCounters:
    def test_successful_rows_count_as_processed(self, db):
        run = _make_run(db, 2)
        run = run_service.process_rows(db, run.id, _rows(2), pipeline=_pipeline(db, _SuccessProvider()))
        assert run.processed == 2
        assert run.failed == 0
        assert run.status == ProcessingStatus.completed.value

    def test_llm_error_row_counts_as_failed_not_processed(self, db):
        """Bug: process_article marked the article failed but returned normally, so
        the run counted it as processed. Article status and run counters disagreed."""
        run = _make_run(db, 1)
        run = run_service.process_rows(db, run.id, _rows(1), pipeline=_pipeline(db, _ErrorProvider()))
        assert run.processed == 0
        assert run.failed == 1

    def test_errored_article_has_failed_status(self, db):
        from app.repositories.article_repo import ArticleRepository

        run = _make_run(db, 1)
        run_service.process_rows(db, run.id, _rows(1), pipeline=_pipeline(db, _ErrorProvider()))
        articles, _ = ArticleRepository(db).list(limit=10, offset=0)
        assert len(articles) == 1
        assert articles[0].status == ArticleStatus.failed.value


class TestReprocessResetsCounters:
    def test_reprocessing_does_not_double_count(self, db):
        """A Celery retry re-enters process_rows for the same run. Counters must be
        reset, not accumulated past total_rows."""
        run = _make_run(db, 2)
        run_service.process_rows(db, run.id, _rows(2), pipeline=_pipeline(db, _SuccessProvider()))
        # Second pass over the same run (rows are now duplicate-hash hits).
        run = run_service.process_rows(db, run.id, _rows(2), pipeline=_pipeline(db, _SuccessProvider()))
        assert run.processed + run.failed <= run.total_rows
        assert run.processed == 2


class TestTerminalState:
    def test_provider_init_failure_marks_run_failed(self, db, monkeypatch):
        """If building the provider/pipeline throws, the run must reach a terminal
        'failed' state, not stay stuck in 'running'."""
        run = _make_run(db, 1)

        def _boom():
            raise RuntimeError("no API key")

        monkeypatch.setattr(run_service, "get_llm_provider", _boom)
        with pytest.raises(RuntimeError):
            run_service.process_rows(db, run.id, _rows(1))

        reloaded = ProcessingRunRepository(db).get(run.id)
        assert reloaded.status == ProcessingStatus.failed.value
        assert reloaded.finished_at is not None

    def test_run_not_found_raises(self, db):
        with pytest.raises(ValueError):
            run_service.process_rows(db, 999999, _rows(1), pipeline=_pipeline(db, _SuccessProvider()))
