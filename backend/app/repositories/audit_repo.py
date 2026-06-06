"""Audit log repository — records pipeline events and analyst actions."""
from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str | int | None = None,
        actor_id: int | None = None,
        before: dict | None = None,
        after: dict | None = None,
        message: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            actor_id=actor_id,
            before=before,
            after=after,
            message=message,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        entity_type: str | None = None,
        action: str | None = None,
    ) -> list[AuditLog]:
        stmt = select(AuditLog)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        stmt = stmt.order_by(desc(AuditLog.created_at), desc(AuditLog.id)).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars())

    def count(
        self,
        *,
        entity_type: str | None = None,
        action: str | None = None,
    ) -> int:
        stmt = select(func.count(AuditLog.id))
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        return self.db.execute(stmt).scalar_one()
