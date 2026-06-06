"""Company endpoints: list (Company Explorer) and detail."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.company_repo import CompanyRepository
from app.schemas.company import (
    AliasOut,
    CompanyDetail,
    CompanyListResponse,
    CompanySummary,
    MentionTimelineEntry,
    SentimentTrendPoint,
)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
def list_companies(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompanyListResponse:
    repo = CompanyRepository(db)
    rows, total = repo.list_with_mentions(limit=limit, offset=offset, search=search)
    return CompanyListResponse(
        items=[
            CompanySummary(
                id=c.id, canonical_name=c.canonical_name, ticker=sym, mention_count=m
            )
            for c, sym, m in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{company_id}", response_model=CompanyDetail)
def get_company(
    company_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompanyDetail:
    repo = CompanyRepository(db)
    company = repo.get(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found.")

    mentions = repo.recent_mentions(company_id)
    trend = repo.sentiment_trend(company_id)

    return CompanyDetail(
        id=company.id,
        canonical_name=company.canonical_name,
        ticker=company.primary_ticker.symbol if company.primary_ticker else None,
        aliases=[AliasOut.model_validate(a) for a in company.aliases],
        mention_count=repo.mention_count(company_id),
        recent_mentions=[
            MentionTimelineEntry(
                article_id=article.id,
                title=article.title,
                sentiment=label,
                created_at=article.created_at,
            )
            for article, label in mentions
        ],
        sentiment_trend=[
            SentimentTrendPoint(label=label, count=count) for label, count in trend
        ],
    )
