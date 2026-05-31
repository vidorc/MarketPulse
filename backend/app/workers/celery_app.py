"""Celery application for background processing (large CSV runs)."""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "marketpulse",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_track_started=True,
    worker_max_tasks_per_child=200,
)

# Ensure task modules are imported so they register with the app.
celery_app.autodiscover_tasks(["app.workers"])

from app.workers import tasks  # noqa: E402,F401  (register tasks)
