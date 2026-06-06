"""Seed ground-truth labels from the bundled benchmark CSV.

The CSV is headerless with columns: title, article_type, company_names, tickers
(the legacy ``mapped_results.csv`` format). Article types are normalized onto the
canonical enum (e.g. ``multi_company_news`` -> ``market_movers``). Idempotent:
labels already present (matched by exact title) are skipped.
"""
from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.enums import LabelSource, normalize_article_type
from app.repositories.benchmark_repo import GroundTruthRepository
from app.services.benchmark.engine import normalize_ticker_set

logger = get_logger("app.seeds.ground_truth")


def _resolve_csv_path() -> Path | None:
    candidates = [
        Path(settings.GROUND_TRUTH_CSV),
        Path(__file__).parent / "data" / "ground_truth_seed.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def seed_ground_truth(db: Session) -> None:
    path = _resolve_csv_path()
    if path is None:
        logger.info("No ground-truth CSV found; skipping.")
        return

    repo = GroundTruthRepository(db)
    existing = {gt.title for gt in repo.all()}
    created = 0

    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if not row or not row[0].strip():
                continue
            title = row[0].strip()
            raw_type = row[1].strip() if len(row) > 1 else ""
            tickers_raw = row[3].strip() if len(row) > 3 else ""
            if title in existing:
                continue
            # Re-serialize tickers through the same normalizer the engine uses so
            # stored labels are canonical (uppercase, comma-joined).
            tickers = ",".join(sorted(normalize_ticker_set(tickers_raw)))
            repo.create(
                title=title,
                expected_tickers=tickers,
                expected_type=normalize_article_type(raw_type).value,
                label_source=LabelSource.seed.value,
            )
            existing.add(title)
            created += 1

    logger.info("Ground-truth labels seeded: %d new (total %d)", created, len(existing))
