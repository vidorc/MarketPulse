"""Groq-backed LLM provider (default).

Carries the retry/backoff and JSON-mode behavior from the legacy script. Real network
calls only fire when ``ALLOW_REAL_LLM`` is true, guarding tests and CI from cost.
"""
from __future__ import annotations

import random
import time

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.base import ExtractionResult, LLMProvider
from app.services.llm.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT,
    build_context,
    parse_response,
)

logger = get_logger("app.services.llm.groq")


def _status_code(exc: Exception) -> int | None:
    """Best-effort HTTP status from a Groq/httpx error, version-agnostic."""
    code = getattr(exc, "status_code", None)
    if code is None:
        resp = getattr(exc, "response", None)
        code = getattr(resp, "status_code", None)
    return code if isinstance(code, int) else None


def _is_retryable(exc: Exception) -> bool:
    """Retry transient failures only. 4xx (except 429) are caller errors — a bad
    API key or malformed request won't fix itself, so retrying just burns time and
    quota. Connection/timeout errors (no status) and 429/5xx are worth retrying."""
    code = _status_code(exc)
    if code is None:
        return True  # connection reset / timeout / DNS — transient
    if code == 429:
        return True
    return code >= 500


def _retry_after_seconds(exc: Exception) -> float | None:
    """Honor a server-provided Retry-After header (seconds form) when present."""
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None)
    if not headers:
        return None
    raw = headers.get("retry-after")
    if raw is None:
        return None
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return None


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self) -> None:
        if not settings.ALLOW_REAL_LLM:
            raise RuntimeError(
                "GroqProvider requested but ALLOW_REAL_LLM is false. "
                "Set ALLOW_REAL_LLM=true (and GROQ_API_KEY) to enable real calls, "
                "or use LLM_PROVIDER=mock."
            )
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is required for GroqProvider.")

        # Imported lazily so the package isn't required when using the mock provider.
        from groq import Groq

        self._client = Groq(api_key=settings.GROQ_API_KEY, timeout=45.0)
        self._model = settings.GROQ_MODEL

    def extract(self, title: str, body: str) -> ExtractionResult:
        context = build_context(title, body, settings.LLM_MAX_CHARS)
        user_content = f"{USER_PROMPT}\n\n{context}"

        max_retries = max(1, settings.LLM_MAX_RETRIES)
        for attempt in range(max_retries):
            try:
                if settings.LLM_REQUEST_DELAY_SECONDS > 0:
                    time.sleep(settings.LLM_REQUEST_DELAY_SECONDS)

                res = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                )
                raw = res.choices[0].message.content.strip()
                return parse_response(raw)
            except Exception as exc:  # noqa: BLE001 — classify, then retry or bail
                last_attempt = attempt == max_retries - 1
                if not _is_retryable(exc):
                    logger.warning(
                        "Groq extract failed with non-retryable error: %s", exc
                    )
                    return ExtractionResult.empty_error(f"Groq error: {exc}")
                if last_attempt:
                    logger.warning(
                        "Groq extract failed (final attempt %d/%d): %s",
                        attempt + 1,
                        max_retries,
                        exc,
                    )
                    break  # no point sleeping after the last try

                # Exponential backoff with jitter; a server Retry-After wins.
                backoff = min(5 * (2**attempt), 60) + random.uniform(0, 1)
                backoff = _retry_after_seconds(exc) or backoff
                logger.warning(
                    "Groq extract failed (attempt %d/%d): %s; backing off %.1fs",
                    attempt + 1,
                    max_retries,
                    exc,
                    backoff,
                )
                time.sleep(backoff)

        return ExtractionResult.empty_error("Groq extraction failed after retries.")
