"""Authentication and user-management endpoints (Phase 2).

- POST /auth/register — self-service signup (always lands as viewer)
- POST /auth/login     — email + password -> JWT
- GET  /auth/me        — current user from the Bearer token
- GET  /auth/users     — list users (admin)
- POST /auth/users     — create user with an explicit role (admin)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    Token,
    UserListResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserOut:
    repo = UserRepository(db)
    if repo.get_by_email(payload.email) is not None:
        raise HTTPException(status_code=409, detail="Email already registered.")
    # Self-registration never grants elevated roles regardless of the request body.
    user = repo.create(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="viewer",
        full_name=payload.full_name,
    )
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    repo = UserRepository(db)
    user = repo.get_by_email(payload.email)
    # Same error whether the email is unknown or the password is wrong — don't leak
    # which accounts exist.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled.")
    token = create_access_token(subject=user.id, role=user.role)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current)


@router.get("/users", response_model=UserListResponse)
def list_users(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserListResponse:
    repo = UserRepository(db)
    users = repo.list(limit=limit, offset=offset)
    return UserListResponse(
        items=[UserOut.model_validate(u) for u in users], total=repo.count()
    )


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: RegisterRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserOut:
    repo = UserRepository(db)
    if repo.get_by_email(payload.email) is not None:
        raise HTTPException(status_code=409, detail="Email already registered.")
    user = repo.create(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,  # admin may set any role here
        full_name=payload.full_name,
    )
    AuditRepository(db).log(
        action="user.create",
        entity_type="user",
        entity_id=user.id,
        actor_id=admin.id,
        after={"email": user.email, "role": user.role},
    )
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)
