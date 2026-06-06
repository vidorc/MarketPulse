"""Analytics dashboard + audit log endpoints (Phase 4).

- GET /analytics  — dashboard aggregations (totals, distributions, top companies)
- GET /audit      — paginated, filterable audit log feed (analyst+)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_analyst
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit_repo import AuditRepository
from app.schemas.analytics import (
    AnalyticsOverviewOut,
    AuditListResponse,
    AuditLogOut,
    LabelCountOut,
    TopCompanyOut,
)
from app.services.analytics.service import AnalyticsService

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsOverviewOut)
def get_analytics(
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalyticsOverviewOut:
    o = AnalyticsService(db).overview()
    lc = lambda xs: [LabelCountOut(label=x.label, count=x.count) for x in xs]  # noqa: E731
    return AnalyticsOverviewOut(
        total_articles=o.total_articles,
        processed_articles=o.processed_articles,
        failed_articles=o.failed_articles,
        total_companies=o.total_companies,
        companies_tagged=o.companies_tagged,
        avg_confidence=o.avg_confidence,
        total_runs=o.total_runs,
        article_types=lc(o.article_types),
        sentiment_distribution=lc(o.sentiment_distribution),
        impact_distribution=lc(o.impact_distribution),
        top_companies=[
            TopCompanyOut(
                company_id=c.company_id,
                name=c.name,
                ticker=c.ticker,
                mentions=c.mentions,
            )
            for c in o.top_companies
        ],
        daily_volume=lc(o.daily_volume),
        confidence_buckets=lc(o.confidence_buckets),
    )


@router.get("/audit", response_model=AuditListResponse)
def list_audit(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    entity_type: str | None = None,
    action: str | None = None,
    _user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
) -> AuditListResponse:
    repo = AuditRepository(db)
    rows = repo.list(
        limit=limit, offset=offset, entity_type=entity_type, action=action
    )
    total = repo.count(entity_type=entity_type, action=action)
    return AuditListResponse(
        items=[
            AuditLogOut(
                id=r.id,
                actor_id=r.actor_id,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                action=r.action,
                before=r.before,
                after=r.after,
                message=r.message,
                created_at=r.created_at.isoformat() if r.created_at else "",
            )
            for r in rows
        ],
        total=total,
    )
