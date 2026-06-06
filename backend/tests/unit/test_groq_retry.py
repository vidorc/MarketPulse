"""Groq provider retry classification.

The legacy retry loop slept on every failure — including non-retryable 4xx (bad
key, malformed request) — and wasted a full backoff after the final attempt. These
tests pin the corrected behavior: bail fast on caller errors, honor Retry-After,
never sleep after the last try.
"""
from __future__ import annotations

import app.services.llm.groq_provider as gp
from app.services.llm.groq_provider import (
    GroqProvider,
    _is_retryable,
    _retry_after_seconds,
    _status_code,
)


class _Resp:
    def __init__(self, status_code=None, headers=None):
        self.status_code = status_code
        self.headers = headers or {}


class _Err(Exception):
    """Mimics a Groq/httpx error carrying status_code and/or a response."""

    def __init__(self, message="boom", status_code=None, response=None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        if response is not None:
            self.response = response


class TestStatusCode:
    def test_reads_direct_status_code(self):
        assert _status_code(_Err(status_code=429)) == 429

    def test_reads_status_from_response(self):
        assert _status_code(_Err(response=_Resp(status_code=503))) == 503

    def test_missing_status_is_none(self):
        assert _status_code(_Err()) is None


class TestIsRetryable:
    def test_connection_error_no_status_is_retryable(self):
        assert _is_retryable(_Err()) is True

    def test_429_is_retryable(self):
        assert _is_retryable(_Err(status_code=429)) is True

    def test_5xx_is_retryable(self):
        assert _is_retryable(_Err(status_code=503)) is True

    def test_401_is_not_retryable(self):
        assert _is_retryable(_Err(status_code=401)) is False

    def test_400_is_not_retryable(self):
        assert _is_retryable(_Err(status_code=400)) is False


class TestRetryAfter:
    def test_parses_numeric_retry_after(self):
        err = _Err(status_code=429, response=_Resp(headers={"retry-after": "12"}))
        assert _retry_after_seconds(err) == 12.0

    def test_absent_header_is_none(self):
        assert _retry_after_seconds(_Err(status_code=429, response=_Resp())) is None

    def test_garbage_header_is_none(self):
        err = _Err(status_code=429, response=_Resp(headers={"retry-after": "soon"}))
        assert _retry_after_seconds(err) is None


def _provider(monkeypatch):
    """Construct a GroqProvider with the cost gate and client stubbed out."""
    monkeypatch.setattr(gp.settings, "ALLOW_REAL_LLM", True, raising=False)
    monkeypatch.setattr(gp.settings, "GROQ_API_KEY", "test-key", raising=False)
    monkeypatch.setattr(gp.settings, "LLM_REQUEST_DELAY_SECONDS", 0, raising=False)
    # Avoid importing the real groq SDK / opening a client.
    prov = GroqProvider.__new__(GroqProvider)
    prov._model = "test-model"
    return prov


class TestExtractRetryLoop:
    def test_non_retryable_error_bails_immediately_without_sleeping(self, monkeypatch):
        prov = _provider(monkeypatch)
        calls = {"create": 0, "sleep": 0}

        def fake_create(**kwargs):
            calls["create"] += 1
            raise _Err("unauthorized", status_code=401)

        monkeypatch.setattr(gp.time, "sleep", lambda s: calls.__setitem__("sleep", calls["sleep"] + 1))

        class _C:
            class chat:
                class completions:
                    create = staticmethod(fake_create)

        prov._client = _C()
        result = prov.extract("title", "body")

        assert result.error is not None
        assert calls["create"] == 1  # no retries on a 401
        assert calls["sleep"] == 0  # and no wasted backoff

    def test_retryable_error_retries_then_gives_up_without_trailing_sleep(self, monkeypatch):
        monkeypatch.setattr(gp.settings, "LLM_MAX_RETRIES", 3, raising=False)
        prov = _provider(monkeypatch)
        calls = {"create": 0, "sleep": 0}

        def fake_create(**kwargs):
            calls["create"] += 1
            raise _Err("rate limited", status_code=429)

        monkeypatch.setattr(gp.time, "sleep", lambda s: calls.__setitem__("sleep", calls["sleep"] + 1))

        class _C:
            class chat:
                class completions:
                    create = staticmethod(fake_create)

        prov._client = _C()
        result = prov.extract("title", "body")

        assert result.error is not None
        assert calls["create"] == 3  # tried all attempts
        assert calls["sleep"] == 2  # slept between attempts, not after the last
