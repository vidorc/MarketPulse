"""User repository — data access for authentication and user management."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.strip().lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def count(self) -> int:
        return self.db.execute(select(func.count(User.id))).scalar_one()

    def list(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        stmt = select(User).order_by(User.id.asc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars())

    def create(
        self,
        *,
        email: str,
        hashed_password: str,
        role: str,
        full_name: str | None = None,
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email.strip().lower(),
            hashed_password=hashed_password,
            role=role,
            full_name=full_name,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.flush()
        return user
