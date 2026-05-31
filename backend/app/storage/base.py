"""Storage abstraction. Local backend now; S3 backend can be added later
without changing callers."""
from abc import ABC, abstractmethod


class Storage(ABC):
    """Pluggable blob storage interface."""

    @abstractmethod
    def save(self, key: str, data: bytes) -> str:
        """Persist bytes under ``key``; return a backend-specific locator."""

    @abstractmethod
    def load(self, key: str) -> bytes:
        """Read bytes previously saved under ``key``."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...
