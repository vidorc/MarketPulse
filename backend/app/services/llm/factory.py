"""LLM provider selection from settings."""
from __future__ import annotations

from app.core.config import settings
from app.services.llm.base import LLMProvider
from app.services.llm.mock import MockProvider


def get_llm_provider() -> LLMProvider:
    """Return the configured provider.

    Defaults to the mock provider whenever real calls are disabled, so the system
    is always runnable without credentials.
    """
    if settings.LLM_PROVIDER == "mock" or not settings.ALLOW_REAL_LLM:
        return MockProvider()
    if settings.LLM_PROVIDER == "groq":
        from app.services.llm.groq_provider import GroqProvider

        return GroqProvider()
    raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
