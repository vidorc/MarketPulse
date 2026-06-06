"""LLM response parsing robustness.

The model is told to emit bare JSON, but in practice wraps it in markdown fences
and occasionally returns the wrong shape for `companies`. The parser must tolerate
that without crashing or fabricating garbage company names.
"""
import pytest

from app.services.llm.prompts import parse_response


class TestParseResponseHappyPath:
    def test_parses_plain_json_object_companies(self):
        raw = (
            '{"article_type": "earnings", "confidence": 99, "impact": "high",'
            ' "reasoning": "r", "companies": [{"name": "REC", "sentiment": "neutral"}]}'
        )
        result = parse_response(raw)
        assert result.article_type == "earnings"
        assert result.confidence == 99
        assert [c.name for c in result.companies] == ["REC"]
        assert result.companies[0].sentiment == "neutral"

    def test_parses_legacy_list_of_strings(self):
        raw = '{"article_type": "company_specific", "confidence": 80, "companies": ["Tata Steel"]}'
        result = parse_response(raw)
        assert [c.name for c in result.companies] == ["Tata Steel"]

    def test_clamps_confidence_to_0_100(self):
        raw = '{"article_type": "earnings", "confidence": 250, "companies": []}'
        assert parse_response(raw).confidence == 100


class TestParseResponseMarkdownFences:
    def test_strips_json_fenced_block(self):
        raw = (
            "```json\n"
            '{"article_type": "earnings", "confidence": 90, "companies": [{"name": "REC"}]}\n'
            "```"
        )
        result = parse_response(raw)
        assert result.article_type == "earnings"
        assert [c.name for c in result.companies] == ["REC"]

    def test_strips_bare_fenced_block(self):
        raw = (
            "```\n"
            '{"article_type": "macro_or_sector", "confidence": 50, "companies": []}\n'
            "```"
        )
        result = parse_response(raw)
        assert result.article_type == "macro_or_sector"
        assert result.companies == []

    def test_tolerates_leading_and_trailing_prose(self):
        raw = 'Here is the JSON:\n{"article_type": "earnings", "confidence": 70, "companies": []}\nDone.'
        result = parse_response(raw)
        assert result.article_type == "earnings"


class TestParseResponseBadCompanyShapes:
    def test_dict_companies_does_not_become_fake_companies_from_keys(self):
        """Bug: a dict for `companies` is truthy, so `x or []` doesn't catch it and
        the loop iterates the dict's KEYS, fabricating companies named after keys."""
        raw = '{"article_type": "earnings", "confidence": 90, "companies": {"name": "REC"}}'
        result = parse_response(raw)
        assert result.companies == []

    def test_string_companies_does_not_iterate_characters(self):
        raw = '{"article_type": "earnings", "confidence": 90, "companies": "REC"}'
        result = parse_response(raw)
        # Must not produce one company per character ("R", "E", "C").
        assert result.companies == []

    def test_null_companies_is_empty(self):
        raw = '{"article_type": "earnings", "confidence": 90, "companies": null}'
        assert parse_response(raw).companies == []

    def test_skips_company_items_without_a_name(self):
        raw = (
            '{"article_type": "earnings", "confidence": 90,'
            ' "companies": [{"sentiment": "positive"}, {"name": "REC"}]}'
        )
        result = parse_response(raw)
        assert [c.name for c in result.companies] == ["REC"]


class TestParseResponseErrors:
    def test_missing_required_keys_raises(self):
        raw = '{"article_type": "earnings"}'  # no confidence, no companies
        with pytest.raises(ValueError):
            parse_response(raw)

    def test_non_json_raises(self):
        with pytest.raises(ValueError):
            parse_response("not json at all")
