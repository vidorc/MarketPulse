"""Bootstrap user seeder.

Creates a single admin account when the users table is empty so a fresh deploy is
reachable. Idempotent: no-ops once any user exists. Credentials come from
ADMIN_EMAIL / ADMIN_PASSWORD settings — change them (or rotate the password) for
any non-local deployment.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models.enums import UserRole
from app.repositories.user_repo import UserRepository

logger = get_logger("app.seeds.users")


def seed_users(db: Session) -> None:
    repo = UserRepository(db)
    if repo.count() > 0:
        logger.info("Users already present; skipping admin bootstrap.")
        return
    repo.create(
        email=settings.ADMIN_EMAIL,
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        role=UserRole.admin.value,
        full_name="MarketPulse Admin",
    )
    logger.info("Seeded bootstrap admin: %s", settings.ADMIN_EMAIL)
