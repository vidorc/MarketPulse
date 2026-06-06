"""Prompt text and response parsing for LLM extraction.

The prompts preserve the rules and few-shot examples from the legacy script, extended
to also request per-company sentiment and an article-level impact level.
"""
from __future__ import annotations

import json
import re

from app.services.llm.base import CompanyExtraction, ExtractionResult

SYSTEM_PROMPT = """You are a financial relevance classifier for NSE-listed companies.
You must classify the article first.
Only output valid JSON.
Never output markdown.
Never output explanations outside JSON."""

USER_PROMPT = """Return all NSE-listed companies that are materially discussed or materially impacted by the article.
The title carries the highest importance when determining the primary subject.

A company should be returned if the article covers its:
- earnings or financial results
- management guidance or corporate commentary
- new major projects, physical operations, or regulatory impact
- acquisitions, mergers, joint ventures, or strategic deals
- explicit stock recommendations
- major specific market impact or target movements

CRITICAL RULES:
1. Do NOT return indices, broad sectors, brokers, analysts, exchanges, unnamed groups, or peers mentioned only for comparison.
2. If the article is strictly technical analysis on broad indices or general macroeconomic updates (FOMC, inflation, general sector themes without specific stocks named), return an empty company list [].
3. Support multi-company extraction: if several named companies are materially discussed, return all of them.

For EACH returned company, assign a sentiment: "positive", "neutral", or "negative".
Assign an overall article impact: "low", "medium", or "high", driven by earnings,
acquisitions, regulatory events, major projects, guidance, or market movement.

article_type must be one of:
company_specific, market_movers, broker_recommendations, technical_analysis,
macro_or_sector, earnings, mergers_and_acquisitions, regulatory, management_commentary

### EXAMPLES:
Title: REC Q4 results: net profit matches estimates
Output: {"article_type": "earnings", "reasoning": "Explicit earnings report", "confidence": 99, "impact": "high", "companies": [{"name": "REC", "sentiment": "neutral"}]}

Title: Adani Ports Q4 preview: High volumes set to boost revenue
Output: {"article_type": "company_specific", "reasoning": "Q4 earnings preview for a named company", "confidence": 94, "impact": "high", "companies": [{"name": "Adani Ports and Special Economic Zone", "sentiment": "positive"}]}

Title: Tata Steel, JSW Steel gain as coal prices rise
Output: {"article_type": "market_movers", "reasoning": "Two named steel companies move on input costs", "confidence": 92, "impact": "medium", "companies": [{"name": "Tata Steel", "sentiment": "positive"}, {"name": "JSW Steel", "sentiment": "positive"}]}

Title: Hot Stocks: Brokerages initiate buy coverage on Adani Ports and Zomato
Output: {"article_type": "broker_recommendations", "reasoning": "Explicit broker buy calls on specific stocks", "confidence": 95, "impact": "medium", "companies": [{"name": "Adani Ports", "sentiment": "positive"}, {"name": "Zomato", "sentiment": "positive"}]}

Title: Taking Stock: Nifty hits fresh record highs led by banks, finance stocks
Output: {"article_type": "macro_or_sector", "reasoning": "Broad index movement, no specific companies", "confidence": 96, "impact": "low", "companies": []}

Title: Technical View: Nifty likely to remain sideways near major hurdles
Output: {"article_type": "technical_analysis", "reasoning": "Broad index technical analysis", "confidence": 98, "impact": "low", "companies": []}

Output strictly as JSON with exactly these keys:
{"article_type": "string", "reasoning": "string", "confidence": number, "impact": "string", "companies": [{"name": "string", "sentiment": "string"}]}"""


def build_context(title: str, body: str, max_chars: int) -> str:
    return f"Title: {title}\nArticle: {body[:max_chars]}"


# Matches a ```json ... ``` or ``` ... ``` fenced block and captures its contents.
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _extract_json(raw_content: str) -> str:
    """Pull a JSON object out of a model response.

    The prompt forbids markdown, but models still wrap output in ``` fences or add
    leading/trailing prose. We try, in order: a fenced block, then the first
    balanced ``{...}`` span, then the raw string as-is.
    """
    text = (raw_content or "").strip()

    fence = _FENCE_RE.search(text)
    if fence:
        text = fence.group(1).strip()

    # If there's surrounding prose, grab the outermost {...} span.
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    return text


def parse_response(raw_content: str) -> ExtractionResult:
    """Parse a model JSON string into an ExtractionResult.

    Tolerant of markdown fences / surrounding prose, and of two company shapes:
    a list of strings (legacy) or a list of ``{"name", "sentiment"}`` objects
    (current prompt). A non-list ``companies`` value (dict, string, null) yields
    no companies rather than fabricating garbage from keys/characters.
    """
    try:
        parsed = json.loads(_extract_json(raw_content))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Response was not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Response JSON was not an object.")

    required = ["article_type", "confidence", "companies"]
    missing = [k for k in required if k not in parsed]
    if missing:
        raise ValueError(f"Missing required JSON keys: {missing}")

    # Only a genuine list yields companies; dict/string/null -> [] (no fabrication).
    raw_companies = parsed.get("companies")
    companies: list[CompanyExtraction] = []
    if isinstance(raw_companies, list):
        for item in raw_companies:
            if isinstance(item, str) and item.strip():
                companies.append(CompanyExtraction(name=item.strip()))
            elif isinstance(item, dict) and item.get("name"):
                companies.append(
                    CompanyExtraction(
                        name=str(item["name"]),
                        sentiment=str(item.get("sentiment", "neutral")),
                    )
                )

    try:
        confidence = int(parsed.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0

    return ExtractionResult(
        article_type=str(parsed.get("article_type", "")),
        companies=companies,
        confidence=max(0, min(100, confidence)),
        reasoning=str(parsed.get("reasoning", "")),
        impact=str(parsed.get("impact", "low")),
        raw_json=raw_content,
    )
