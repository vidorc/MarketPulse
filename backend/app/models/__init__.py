"""Model package — imports every model so SQLAlchemy's registry is always complete.

Importing any single model (e.g. ``from app.models.article import Article``) runs
this ``__init__``, which registers all models. This prevents string-based
relationships (e.g. ``"ProcessingRun"``) from failing to resolve when only a subset
of modules has been imported.
"""
from app.models.alias import Alias
from app.models.article import (
    Article,
    ArticleCompany,
    Classification,
    Sentiment,
)
from app.models.audit import AuditLog
from app.models.benchmark import BenchmarkResult, GroundTruth
from app.models.company import Company, Ticker
from app.models.processing_run import ProcessingRun
from app.models.user import User

__all__ = [
    "Alias",
    "Article",
    "ArticleCompany",
    "Classification",
    "Sentiment",
    "AuditLog",
    "BenchmarkResult",
    "GroundTruth",
    "Company",
    "Ticker",
    "ProcessingRun",
    "User",
]
