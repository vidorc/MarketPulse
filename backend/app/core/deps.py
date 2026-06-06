"""Auth dependencies: extract the current user from a Bearer token and enforce roles.

``get_current_user`` validates the JWT and loads the user; ``require_role`` builds a
dependency that additionally checks the user's role. Role hierarchy is
admin > analyst > viewer, so a higher role satisfies a lower requirement.
"""
from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repo import UserRepository

# auto_error=False so we can return 401 with a clean message rather than the
# default 403 when the header is missing.
_bearer = HTTPBearer(auto_error=False)

# Higher number = more privilege. A guard requiring `analyst` admits admins too.
_ROLE_RANK: dict[str, int] = {
    UserRole.viewer.value: 0,
    UserRole.analyst.value: 1,
    UserRole.admin.value: 2,
}

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise _CREDENTIALS_EXC
    claims = decode_access_token(creds.credentials)
    if claims is None or "sub" not in claims:
        raise _CREDENTIALS_EXC
    try:
        user_id = int(claims["sub"])
    except (TypeError, ValueError):
        raise _CREDENTIALS_EXC from None
    user = UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC
    return user


def require_role(minimum: UserRole) -> Callable[..., User]:
    """Dependency factory enforcing a minimum role on the current user."""
    needed = _ROLE_RANK[minimum.value]

    def _guard(user: User = Depends(get_current_user)) -> User:
        if _ROLE_RANK.get(user.role, -1) < needed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {minimum.value} role or higher.",
            )
        return user

    return _guard


# Convenience guards for common requirements.
require_analyst = require_role(UserRole.analyst)
require_admin = require_role(UserRole.admin)
