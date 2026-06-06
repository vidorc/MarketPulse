"""Deterministic mock LLM provider for tests and offline development.

Returns canned :class:`ExtractionResult`s keyed by substrings found in the title.
Falls back to a neutral macro/empty extraction so the pipeline always gets a valid
result without any network call.
"""
from __future__ import annotations

import json

from app.services.llm.base import CompanyExtraction, ExtractionResult, LLMProvider

# (title substring, ExtractionResult factory). First match wins.
_FIXTURES: list[tuple[str, dict]] = [
    (
        "adani ports",
        {
            "article_type": "company_specific",
            "reasoning": "Q4 earnings preview for a named company.",
            "confidence": 94,
            "impact": "high",
            "companies": [{"name": "Adani Ports and Special Economic Zone", "sentiment": "positive"}],
        },
    ),
    (
        "tata steel",
        {
            "article_type": "market_movers",
            "reasoning": "Two named steel companies move on input costs.",
            "confidence": 90,
            "impact": "medium",
            "companies": [
                {"name": "Tata Steel", "sentiment": "positive"},
                {"name": "JSW Steel", "sentiment": "positive"},
            ],
        },
    ),
    (
        "rec q4",
        {
            "article_type": "earnings",
            "reasoning": "Explicit earnings report.",
            "confidence": 99,
            "impact": "high",
            "companies": [{"name": "REC", "sentiment": "neutral"}],
        },
    ),
    (
        "nifty",
        {
            "article_type": "macro_or_sector",
            "reasoning": "Broad index movement, no specific companies.",
            "confidence": 96,
            "impact": "low",
            "companies": [],
        },
    ),
]


class MockProvider(LLMProvider):
    name = "mock"

    def extract(self, title: str, body: str) -> ExtractionResult:
        low = (title or "").lower()
        payload: dict | None = None
        for needle, data in _FIXTURES:
            if needle in low:
                payload = data
                break
        if payload is None:
            payload = {
                "article_type": "macro_or_sector",
                "reasoning": "No specific named companies detected (mock default).",
                "confidence": 50,
                "impact": "low",
                "companies": [],
            }

        companies = [
            CompanyExtraction(name=c["name"], sentiment=c.get("sentiment", "neutral"))
            for c in payload["companies"]
        ]
        return ExtractionResult(
            article_type=payload["article_type"],
            companies=companies,
            confidence=payload["confidence"],
            reasoning=payload["reasoning"],
            impact=payload["impact"],
            raw_json=json.dumps(payload),
        )
