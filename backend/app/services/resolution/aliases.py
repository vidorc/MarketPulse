"""Alias normalization and generation.

Ports the canonical-registry logic from the legacy ``company_mapper_llm.py`` into a
reusable, testable module. The generated aliases are persisted to the ``aliases``
table by the seeder; lookups happen against that table at resolution time.
"""
import re

# Corporate suffixes/qualifiers dropped when deriving short aliases.
_STRIP_PATTERN = re.compile(
    r"\b(limited|ltd|corp|corporation|inc|co|company|india|industries|industry|"
    r"services|service|holdings|holding|financial|financials|group|energy|power|"
    r"telecom|technologies|technology)\b",
    re.IGNORECASE,
)

# Generic words that must never resolve to a specific company.
# e.g. "State Bank of India" must not be reachable via "state".
UNSAFE_SHORTS: set[str] = {
    "bank",
    "bank of",
    "state",
    "state bank",
    "p and g",
    "the",
    "housing",
    "development",
    "finance",
    "india",
    "national",
    "general",
}

# Connector/preposition words a derived alias must never end on. An alias dangling
# on one of these ("state bank of") is both meaningless and a collision magnet, so
# we strip trailing connectors before deciding whether a derived form is safe.
_CONNECTORS: set[str] = {"of", "and", "the", "for", "to", "in", "on", "at", "by"}

# Individual generic tokens. A *multi-word* derived alias made up entirely of these
# ("housing development", "state bank") is just as dangerous as a single generic
# word — it collides across many companies — but exact-membership against
# UNSAFE_SHORTS can't catch every such combination. We reject any derived alias
# whose every token is generic. Built from the words in UNSAFE_SHORTS plus
# connectors so the two stay in sync.
_GENERIC_TOKENS: set[str] = {w for s in UNSAFE_SHORTS for w in s.split()} | _CONNECTORS

# Curated short-forms / acronyms -> canonical NSE company name.
CURATED_ACRONYMS: dict[str, str] = {
    "m&m": "Mahindra & Mahindra Limited",
    "mahindra and mahindra": "Mahindra & Mahindra Limited",
    "ioc": "Indian Oil Corporation Limited",
    "iocl": "Indian Oil Corporation Limited",
    "hul": "Hindustan Unilever Limited",
    "sbi": "State Bank of India",
    "ril": "Reliance Industries Limited",
    "tcs": "Tata Consultancy Services Limited",
    "infy": "Infosys Limited",
    "l&t": "Larsen & Toubro Limited",
    "adani ports": "Adani Ports and Special Economic Zone Limited",
    "adani ports and sez": "Adani Ports and Special Economic Zone Limited",
    "indiamart": "IndiaMART InterMESH Limited",
    "rec ltd": "REC Limited",
    "rec": "REC Limited",
    "gillette": "Gillette India Limited",
    "gillette india": "Gillette India Limited",
    "havells": "Havells India Limited",
    "havells india": "Havells India Limited",
    "ambuja": "Ambuja Cements Limited",
    "ambuja cements": "Ambuja Cements Limited",
    "au": "AU Small Finance Bank Limited",
    "au bank": "AU Small Finance Bank Limited",
    "ujjivan": "Ujjivan Small Finance Bank Limited",
    "ujjivan sfb": "Ujjivan Small Finance Bank Limited",
    "whirlpool": "Whirlpool of India Limited",
    "whirlpool india": "Whirlpool of India Limited",
    "abb": "ABB India Limited",
    "abb india": "ABB India Limited",
    "tata comm": "Tata Communications Limited",
    "tata communications": "Tata Communications Limited",
    "adani energy": "Adani Energy Solutions Limited",
    "adani energy solutions": "Adani Energy Solutions Limited",
    "p&g hygiene": "Procter & Gamble Hygiene and Health Care Limited",
    "p and g hygiene": "Procter & Gamble Hygiene and Health Care Limited",
}


def normalize_alias(text: str) -> str:
    """Standardize a string for deterministic dictionary/DB lookups."""
    t = str(text).strip().lower()
    t = t.replace("&", " and ")
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _trim_connectors(alias: str) -> str:
    """Drop trailing connector words so a derived alias never dangles on one.

    'state bank of' -> 'state bank'. Applied before the safety check so that the
    *trimmed* form is what gets validated against UNSAFE_SHORTS.
    """
    parts = alias.split()
    while parts and parts[-1] in _CONNECTORS:
        parts.pop()
    return " ".join(parts)


def _is_safe_short(alias: str) -> bool:
    """A derived short alias is safe only if it is long enough, not generic, and
    does not end on a connector word."""
    if len(alias) <= 3:
        return False
    if alias in UNSAFE_SHORTS:
        return False
    parts = alias.split()
    if parts and parts[-1] in _CONNECTORS:
        return False
    # Reject combinations that are generic through-and-through, even when the exact
    # phrase isn't enumerated in UNSAFE_SHORTS ("housing development", "state bank").
    if parts and all(p in _GENERIC_TOKENS for p in parts):
        return False
    return True


def generate_aliases(canonical_name: str, symbol: str) -> set[str]:
    """Return the set of normalized aliases for a company.

    Always includes the normalized canonical name and symbol. Adds a
    suffix-stripped form and a safe last-word-removed form, skipping anything in
    :data:`UNSAFE_SHORTS`, ending on a connector, or shorter than the safety
    threshold.
    """
    aliases: set[str] = set()

    norm_name = normalize_alias(canonical_name)
    norm_symbol = normalize_alias(symbol)
    if norm_name:
        aliases.add(norm_name)
    if norm_symbol:
        aliases.add(norm_symbol)

    # Suffix-stripped base name, e.g. "Ambuja Cements Limited" -> "ambuja cements".
    clean = _STRIP_PATTERN.sub("", canonical_name.lower()).strip()
    clean = re.sub(r"[^\w\s]+$", "", clean).strip()
    clean_norm = _trim_connectors(normalize_alias(clean))

    if _is_safe_short(clean_norm):
        aliases.add(clean_norm)

        # Safe last-word removal: "ambuja cements" -> "ambuja".
        parts = clean_norm.split()
        if len(parts) > 1:
            shortened = _trim_connectors(" ".join(parts[:-1]))
            if _is_safe_short(shortened) and len(shortened) >= 4:
                aliases.add(shortened)

    # Final guard: never emit an unsafe/empty/connector-dangling alias, regardless
    # of how it was derived.
    return {
        a
        for a in aliases
        if a and a not in UNSAFE_SHORTS and a.split()[-1] not in _CONNECTORS
    }
