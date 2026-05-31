"""Seed orchestrator. Runs all registered seeders in order.

Each phase adds a seeder function to ``SEEDERS``. Running this module is
idempotent: individual seeders must no-op when their data already exists.

Usage:  python -m app.seeds.seed_all
"""
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal

logger = get_logger("app.seeds")

# (name, callable taking a Session). Populated as phases land their seeders.
SEEDERS: list[tuple[str, Callable[[Session], None]]] = []


def _load_seeders() -> None:
    """Import seeder modules so they append to SEEDERS. Tolerant of absent
    modules during early phases."""
    SEEDERS.clear()
    try:
        from app.seeds.seed_companies import seed_companies

        SEEDERS.append(("companies", seed_companies))
    except ImportError:
        logger.info("seed_companies not present yet; skipping")

    try:
        from app.seeds.seed_users import seed_users

        SEEDERS.append(("users", seed_users))
    except ImportError:
        logger.info("seed_users not present yet; skipping")

    try:
        from app.seeds.seed_ground_truth import seed_ground_truth

        SEEDERS.append(("ground_truth", seed_ground_truth))
    except ImportError:
        logger.info("seed_ground_truth not present yet; skipping")


def run() -> None:
    _load_seeders()
    if not SEEDERS:
        logger.info("No seeders registered.")
        return
    db = SessionLocal()
    try:
        for name, fn in SEEDERS:
            logger.info("Seeding: %s", name)
            fn(db)
            db.commit()
        logger.info("Seeding complete (%d seeders).", len(SEEDERS))
    except Exception:
        db.rollback()
        logger.exception("Seeding failed; rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
