"""Storage backend selection."""
from functools import lru_cache

from app.core.config import settings
from app.storage.base import Storage
from app.storage.local import LocalStorage


@lru_cache
def get_storage() -> Storage:
    if settings.STORAGE_BACKEND == "local":
        return LocalStorage(settings.STORAGE_LOCAL_DIR)
    # Future: S3Storage(...) keyed on settings.STORAGE_BACKEND == "s3".
    raise ValueError(f"Unsupported storage backend: {settings.STORAGE_BACKEND}")
