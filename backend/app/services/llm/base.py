"""LLM extraction interface and shared result types.

The pipeline depends only on :class:`LLMProvider`; concrete providers (Groq, mock,
and future Claude/OpenAI) are selected by the factory from settings.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CompanyExtraction:
    """One company the model judged materially relevant, with its sentiment."""

    name: str
    sentiment: str = "neutral"  # positive | neutral | negative


@dataclass
class ExtractionResult:
    """Normalized output of an LLM extraction call."""

    article_type: str
    companies: list[CompanyExtraction]
    confidence: int
    reasoning: str
    impact: str = "low"  # low | medium | high
    raw_json: str = ""
    error: str | None = None

    @property
    def company_names(self) -> list[str]:
        return [c.name for c in self.companies]

    @classmethod
    def empty_error(cls, message: str) -> ExtractionResult:
        return cls(
            article_type="error",
            companies=[],
            confidence=0,
            reasoning=message,
            impact="low",
            raw_json="",
            error=message,
        )


class LLMProvider(ABC):
    """Extracts companies, type, sentiment, impact, and confidence from an article."""

    name: str = "base"

    @abstractmethod
    def extract(self, title: str, body: str) -> ExtractionResult:
        ...
