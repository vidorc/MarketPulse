"""Seed companies, tickers, and generated aliases from the NSE registry CSV.

Idempotent: existing companies (matched by canonical name) and aliases (matched by
normalized form) are skipped, so re-running only fills gaps.
"""
from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.alias import Alias
from app.models.company import Company, Ticker
from app.models.enums import AliasSource
from app.services.resolution.aliases import (
    CURATED_ACRONYMS,
    generate_aliases,
    normalize_alias,
)

logger = get_logger("app.seeds.companies")


def _resolve_csv_path() -> Path:
    """Find the NSE CSV via settings, falling back to the bundled seed copy."""
    candidates = [
        Path(settings.NSE_COMPANIES_CSV),
        Path(__file__).parent / "data" / "nse_companies.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"NSE companies CSV not found. Tried: {[str(c) for c in candidates]}"
    )


def seed_companies(db: Session) -> None:
    path = _resolve_csv_path()
    logger.info("Seeding companies from %s", path)

    existing_companies = {
        name for (name,) in db.execute(select(Company.canonical_name)).all()
    }
    existing_aliases = {a for (a,) in db.execute(select(Alias.normalized)).all()}

    # name -> Company, for curated-acronym wiring after the main pass.
    name_to_company: dict[str, Company] = {}
    created = 0

    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        # NSE headers carry leading spaces ("  SERIES"); normalize keys.
        for raw_row in reader:
            row = { (k or "").strip(): (v or "").strip() for k, v in raw_row.items() }
            symbol = row.get("SYMBOL", "").upper()
            canonical = row.get("NAME OF COMPANY", "")
            if not symbol or not canonical:
                continue
            if canonical in existing_companies:
                continue

            company = Company(canonical_name=canonical)
            db.add(company)
            db.flush()  # assign company.id

            ticker = Ticker(
                symbol=symbol,
                company_id=company.id,
                series=row.get("SERIES") or None,
                isin=row.get("ISIN NUMBER") or None,
                face_value=row.get("FACE VALUE") or None,
            )
            db.add(ticker)
            db.flush()  # assign ticker.id

            company.primary_ticker_id = ticker.id
            name_to_company[canonical] = company
            existing_companies.add(canonical)
            created += 1

            for norm in generate_aliases(canonical, symbol):
                if norm in existing_aliases:
                    continue
                db.add(
                    Alias(
                        company_id=company.id,
                        alias_text=norm,
                        normalized=norm,
                        source=AliasSource.generated.value,
                    )
                )
                existing_aliases.add(norm)

    db.flush()
    _seed_curated_aliases(db, existing_aliases)
    logger.info("Companies seeded: %d new (aliases total now %d)", created, len(existing_aliases))


def _seed_curated_aliases(db: Session, existing_aliases: set[str]) -> None:
    """Wire curated acronyms to their canonical companies if present."""
    added = 0
    for alias, canonical_name in CURATED_ACRONYMS.items():
        norm_alias = normalize_alias(alias)
        if norm_alias in existing_aliases:
            continue
        company = db.execute(
            select(Company).where(Company.canonical_name == canonical_name)
        ).scalar_one_or_none()
        if company is None:
            # Curated name not in this NSE snapshot; skip quietly.
            continue
        db.add(
            Alias(
                company_id=company.id,
                alias_text=norm_alias,
                normalized=norm_alias,
                source=AliasSource.acronym.value,
            )
        )
        existing_aliases.add(norm_alias)
        added += 1
    if added:
        logger.info("Curated acronym aliases added: %d", added)
