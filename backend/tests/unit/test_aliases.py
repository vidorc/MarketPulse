"""Alias generation and normalization — including the dangerous-alias guards.

These guards are load-bearing: a leak here silently mis-maps news to the wrong
company (e.g. resolving "State Bank of India" via a generic "state bank of").
"""
from app.services.resolution.aliases import (
    UNSAFE_SHORTS,
    generate_aliases,
    normalize_alias,
)


class TestNormalizeAlias:
    def test_lowercases_and_collapses_whitespace(self):
        assert normalize_alias("  Tata   Steel  ") == "tata steel"

    def test_ampersand_becomes_and(self):
        assert normalize_alias("M&M") == "m and m"

    def test_strips_punctuation(self):
        assert normalize_alias("Larsen & Toubro Ltd.") == "larsen and toubro ltd"


class TestGenerateAliases:
    def test_includes_normalized_name_and_symbol(self):
        out = generate_aliases("Tata Steel Limited", "TATASTEEL")
        assert "tata steel limited" in out
        assert "tatasteel" in out

    def test_includes_suffix_stripped_form(self):
        out = generate_aliases("Ambuja Cements Limited", "AMBUJACEM")
        assert "ambuja cements" in out

    def test_includes_safe_last_word_removed_form(self):
        out = generate_aliases("Ambuja Cements Limited", "AMBUJACEM")
        assert "ambuja" in out

    def test_never_emits_an_unsafe_generic(self):
        out = generate_aliases("Bank of Baroda", "BANKBARODA")
        assert "bank" not in out
        assert "bank of" not in out

    def test_state_bank_of_india_does_not_leak_a_generic_partial(self):
        """The bug: stripping 'india' yields 'state bank of', which is generic and
        was not in UNSAFE_SHORTS, so it leaked as a resolvable alias for SBI."""
        out = generate_aliases("State Bank of India", "SBIN")
        assert "state bank of" not in out
        assert "state bank" not in out
        assert "state" not in out

    def test_no_derived_alias_ends_in_a_connector_word(self):
        """A derived alias dangling on a preposition/connector ('... of', '... and')
        is meaningless and a collision risk; none should survive."""
        out = generate_aliases("State Bank of India", "SBIN")
        connectors = {"of", "and", "the", "for", "to"}
        for alias in out:
            last = alias.split()[-1] if alias.split() else ""
            assert last not in connectors, f"{alias!r} ends in a connector"

    def test_unsafe_shorts_are_never_in_output(self):
        # Property: across a spread of names, no UNSAFE_SHORTS value is ever emitted.
        names = [
            ("Housing Development Finance Corporation Limited", "HDFC"),
            ("National Aluminium Company Limited", "NATIONALUM"),
            ("General Insurance Corporation of India", "GICRE"),
        ]
        for name, sym in names:
            out = generate_aliases(name, sym)
            assert out.isdisjoint(UNSAFE_SHORTS), f"{name} leaked {out & UNSAFE_SHORTS}"

    def test_all_generic_token_combination_is_rejected(self):
        """A derived alias whose every token is generic ('housing development')
        collides across many companies even though the exact phrase isn't enumerated
        in UNSAFE_SHORTS. The all-generic guard must drop it."""
        out = generate_aliases("Housing Development Finance Corporation Limited", "HDFC")
        assert "housing development" not in out
        assert "housing" not in out
        assert "development" not in out
