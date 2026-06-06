"""Article endpoints: upload, process, list, detail, manual correction."""
from __future__ import annotations

from pathlib import PurePosixPath
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, require_analyst
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.repositories.article_repo import ArticleRepository
from app.repositories.audit_repo import AuditRepository
from app.schemas.article import (
    ArticleDetail,
    ArticleListResponse,
    CorrectionRequest,
    CsvValidationResponse,
    ProcessRequest,
    ProcessRunResponse,
)
from app.schemas.mappers import article_to_detail, article_to_summary
from app.services.pipeline import ingestion, run_service
from app.storage.factory import get_storage

logger = get_logger("app.api.articles")
router = APIRouter(prefix="/articles", tags=["articles"])

# In-process staging of validated rows keyed by run_id, so /process can run the
# exact rows the analyst previewed without re-uploading. For multi-worker
# deployments this would move to Redis; fine for single-process dev/runs.
_STAGED_ROWS: dict[int, list[ingestion.CsvRow]] = {}

# Read uploads in bounded chunks so an oversized file is rejected before it is
# fully materialized in memory.
_CHUNK = 64 * 1024


async def _read_capped(file: UploadFile, max_bytes: int) -> bytes:
    """Read an upload, rejecting with 413 once it exceeds ``max_bytes``.

    Reads incrementally and bails after at most one chunk past the cap, so a
    multi-GB upload can never exhaust memory on this unauthenticated endpoint.
    """
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds the {max_bytes}-byte upload limit.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _unique_storage_key(filename: str) -> str:
    """Build a collision-free storage key from a user-supplied filename.

    Strips any path components and prefixes a random token so two uploads of the
    same name never overwrite each other.
    """
    base = PurePosixPath(filename.replace("\\", "/")).name or "upload.csv"
    return f"uploads/{uuid4().hex}_{base}"


@router.post("/upload", response_model=CsvValidationResponse)
async def upload_csv(
    file: UploadFile = File(...),
    _user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
) -> CsvValidationResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    content = await _read_capped(file, settings.MAX_UPLOAD_BYTES)
    report, rows = ingestion.validate_csv(content)

    if not report.valid:
        # Return the validation report so the UI can show issues; no run created.
        return CsvValidationResponse(**report.__dict__, run_id=None)

    # Persist the raw file under a unique key and stage the run for processing.
    storage = get_storage()
    storage_key = _unique_storage_key(file.filename)
    storage.save(storage_key, content)

    run = run_service.create_run(
        db,
        source_filename=file.filename,
        storage_key=storage_key,
        total_rows=len(rows),
    )
    _STAGED_ROWS[run.id] = rows

    return CsvValidationResponse(**report.__dict__, run_id=run.id)


@router.post("/process", response_model=ProcessRunResponse)
def process_run(
    payload: ProcessRequest,
    _user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
) -> ProcessRunResponse:
    rows = _STAGED_ROWS.get(payload.run_id)
    if rows is None:
        raise HTTPException(
            status_code=404,
            detail="No staged rows for this run_id. Re-upload the file.",
        )

    if payload.async_mode:
        from app.workers.tasks import process_run_task

        process_run_task.delay(
            payload.run_id,
            [
                {"title": r.title, "body": r.body, "url": r.url, "source": r.source}
                for r in rows
            ],
        )
        from app.repositories.processing_run_repo import ProcessingRunRepository

        run = ProcessingRunRepository(db).get(payload.run_id)
        return ProcessRunResponse(
            run_id=run.id,
            status="queued",
            total_rows=run.total_rows,
            processed=run.processed,
            failed=run.failed,
        )

    run = run_service.process_rows(db, payload.run_id, rows)
    _STAGED_ROWS.pop(payload.run_id, None)
    return ProcessRunResponse(
        run_id=run.id,
        status=run.status,
        total_rows=run.total_rows,
        processed=run.processed,
        failed=run.failed,
    )


@router.get("", response_model=ArticleListResponse)
def list_articles(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    article_type: str | None = None,
    status: str | None = None,
    search: str | None = None,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ArticleListResponse:
    repo = ArticleRepository(db)
    items, total = repo.list(
        limit=limit,
        offset=offset,
        article_type=article_type,
        status=status,
        search=search,
    )
    return ArticleListResponse(
        items=[article_to_summary(a) for a in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{article_id}", response_model=ArticleDetail)
def get_article(
    article_id: int,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ArticleDetail:
    article = ArticleRepository(db).get(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found.")
    return article_to_detail(article)


@router.post("/{article_id}/corrections", response_model=ArticleDetail)
def correct_article(
    article_id: int,
    payload: CorrectionRequest,
    user: User = Depends(require_analyst),
    db: Session = Depends(get_db),
) -> ArticleDetail:
    """Apply an analyst correction: replace the article's company links with the
    given tickers. Records an audit entry attributed to the acting analyst."""
    from sqlalchemy import select

    from app.models.article import ArticleCompany
    from app.models.company import Ticker

    repo = ArticleRepository(db)
    article = repo.get(article_id)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found.")

    before = [ac.ticker.symbol for ac in article.article_companies if ac.ticker]

    # Remove existing links, add corrected ones.
    for ac in list(article.article_companies):
        db.delete(ac)
    db.flush()

    applied: list[str] = []
    for symbol in payload.tickers:
        ticker = db.execute(
            select(Ticker).where(Ticker.symbol == symbol.strip().upper())
        ).scalar_one_or_none()
        if ticker is None:
            continue
        db.add(
            ArticleCompany(
                article_id=article.id,
                company_id=ticker.company_id,
                ticker_id=ticker.id,
                alias_used=None,
                confidence=100,
                is_manual_correction=True,
            )
        )
        applied.append(ticker.symbol)

    if payload.article_type and article.classification:
        article.classification.article_type = payload.article_type

    AuditRepository(db).log(
        action="article_corrected",
        entity_type="article",
        entity_id=article.id,
        actor_id=user.id,
        before={"tickers": before},
        after={"tickers": applied, "article_type": payload.article_type},
        message="Manual analyst correction.",
    )
    db.commit()

    article = repo.get(article_id)
    return article_to_detail(article)
