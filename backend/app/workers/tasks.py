"""Celery task definitions.

Phase 0 ships the registration surface; the real processing task is wired in
Phase 1 once the pipeline service exists.
"""
from app.core.logging import get_logger

logger = get_logger("app.workers.tasks")


def register_tasks() -> None:
    """Hook for task registration; tasks self-register via decorators below."""
