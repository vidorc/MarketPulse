"""Company resolution service — maps an extracted company string to a company,
ticker, and the alias that matched.

Lookups go against the ``aliases`` table (seeded once from the NSE registry). An
in-process cache keeps the normalized-alias -> (company_id, ticker, name) map hot;
it can be invalidated when aliases change.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alias import Alias
from app.models.company import Company, Ticker
from app.services.resolution.aliases import normalize_alias


@dataclass(frozen=True)
class ResolvedCompany:
    company_id: int
    company_name: str
    ticker_id: int | None
    ticker_symbol: str | None
    alias_used: str


class ResolutionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._cache: dict[str, ResolvedCompany] | None = None

    def _build_cache(self) -> dict[str, ResolvedCompany]:
        """Load active aliases joined to company + primary ticker into memory.

        Ordered by (normalized, company_id) and inserted first-writer-wins so an
        ambiguous alias shared by several companies always resolves to the same
        (lowest company_id) company across reloads. Without this, dict-overwrite
        order followed the DB's row order and the mapping was nondeterministic.
        """
        stmt = (
            select(
                Alias.normalized,
                Alias.alias_text,
                Company.id,
                Company.canonical_name,
                Ticker.id,
                Ticker.symbol,
            )
            .join(Company, Alias.company_id == Company.id)
            .join(Ticker, Company.primary_ticker_id == Ticker.id, isouter=True)
            .where(Alias.is_active.is_(True))
            .order_by(Alias.normalized.asc(), Company.id.asc())
        )
        cache: dict[str, ResolvedCompany] = {}
        for normalized, alias_text, cid, cname, tid, tsym in self.db.execute(stmt):
            if normalized in cache:
                continue  # first (lowest company_id) wins — deterministic
            cache[normalized] = ResolvedCompany(
                company_id=cid,
                company_name=cname,
                ticker_id=tid,
                ticker_symbol=tsym,
                alias_used=alias_text,
            )
        return cache

    @property
    def cache(self) -> dict[str, ResolvedCompany]:
        if self._cache is None:
            self._cache = self._build_cache()
        return self._cache

    def invalidate(self) -> None:
        self._cache = None

    def resolve(self, name: str) -> ResolvedCompany | None:
        """Resolve a raw extracted company name. Returns None on a miss."""
        if not name or not name.strip():
            return None
        return self.cache.get(normalize_alias(name))

    def resolve_many(self, names: list[str]) -> tuple[list[ResolvedCompany], list[str]]:
        """Resolve a list of names. Returns (resolved, misses).

        Resolved entries are de-duplicated by company_id (first match wins),
        preserving order.
        """
        resolved: list[ResolvedCompany] = []
        misses: list[str] = []
        seen: set[int] = set()
        for name in names:
            hit = self.resolve(name)
            if hit is None:
                misses.append(name)
            elif hit.company_id not in seen:
                seen.add(hit.company_id)
                resolved.append(hit)
        return resolved, misses
