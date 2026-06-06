"""Shared pytest fixtures.

Tests run against an in-memory SQLite database built from the ORM metadata, so the
suite is fast, deterministic, and needs no external Postgres. The LLM is always the
deterministic MockProvider here — no network, no spend.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.base_registry import import_all_models

# Ensure every model is registered on Base.metadata before create_all.
import_all_models()


@pytest.fixture()
def db() -> Session:
    """A fresh in-memory SQLite session with all tables created.

    Uses StaticPool + check_same_thread=False so every connection shares ONE
    in-memory database — without it, SQLite hands each connection (and each
    TestClient worker thread) its own empty DB and tables "disappear". Foreign
    keys are enabled so cascade/constraint behavior matches Postgres closely.
    """
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_conn, _record):  # noqa: ANN001
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    SessionTesting = sessionmaker(bind=engine, autoflush=False, future=True)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()
        # Drop with FK enforcement off: companies<->tickers is a circular FK, and
        # SQLite's implicit per-table DELETE during DROP would otherwise trip the
        # constraint once both tables hold linked rows.
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
            Base.metadata.drop_all(conn)
            conn.commit()
        engine.dispose()


@pytest.fixture()
def make_user(db):
    """Factory creating a persisted user with a given role. Returns the User."""
    from app.core.security import hash_password
    from app.models.user import User

    def _make(
        email: str = "analyst@test.io",
        password: str = "password123",
        role: str = "analyst",
        is_active: bool = True,
        full_name: str | None = None,
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hash_password(password),
            role=role,
            is_active=is_active,
            full_name=full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


def _build_app(db, tmp_path, monkeypatch):
    """Construct a TestClient app wired to the in-memory db + temp storage."""
    from app.api.v1.endpoints import articles as articles_ep
    from app.db.session import get_db
    from app.main import create_app
    from app.storage.local import LocalStorage

    storage = LocalStorage(str(tmp_path / "uploads"))
    monkeypatch.setattr(articles_ep, "get_storage", lambda: storage)
    articles_ep._STAGED_ROWS.clear()

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    return app


@pytest.fixture()
def client(db, tmp_path, monkeypatch, make_user):
    """A FastAPI TestClient authenticated as an analyst by default.

    Most endpoint tests exercise analyst-level operations; overriding
    ``get_current_user`` to a persisted analyst keeps them focused on behavior
    rather than re-doing the login dance every test. Auth/RBAC itself is tested
    explicitly via the ``raw_client`` fixture (no override).
    """
    from fastapi.testclient import TestClient

    from app.core.deps import get_current_user

    app = _build_app(db, tmp_path, monkeypatch)
    analyst = make_user(email="default-analyst@test.io", role="analyst")
    app.dependency_overrides[get_current_user] = lambda: analyst

    with TestClient(app) as c:
        c.current_user = analyst  # type: ignore[attr-defined]
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def raw_client(db, tmp_path, monkeypatch):
    """A TestClient with NO auth override — real Bearer-token flow and role guards
    apply. Use this to test login, 401s, and RBAC enforcement."""
    from fastapi.testclient import TestClient

    app = _build_app(db, tmp_path, monkeypatch)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def auth_header():
    """Build an Authorization header for a given user."""
    from app.core.security import create_access_token

    def _header(user) -> dict[str, str]:
        token = create_access_token(subject=user.id, role=user.role)
        return {"Authorization": f"Bearer {token}"}

    return _header
