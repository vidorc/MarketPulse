"""Password hashing and JWT issuance/verification.

Uses the ``bcrypt`` library directly rather than passlib: the installed passlib
(1.7.4) is incompatible with bcrypt 5.x (its version shim was removed and the
72-byte path now raises). bcrypt's own API is small and stable, so we depend on it
directly. Passwords are truncated to bcrypt's 72-byte hard limit before hashing.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# bcrypt silently ignores bytes past 72; truncate explicitly so a long password
# and its 72-byte prefix aren't treated as the same secret implicitly.
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_to_bcrypt_bytes(password), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(password), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    *, subject: str | int, role: str, expires_minutes: int | None = None
) -> str:
    """Issue a signed JWT carrying the user id (``sub``) and ``role``."""
    expire_minutes = (
        expires_minutes
        if expires_minutes is not None
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Return the token claims, or None if the token is invalid/expired."""
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None
