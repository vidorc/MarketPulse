"""add indexes on foreign keys

Postgres does not auto-create indexes on FK columns. The hot read paths —
Company Explorer (mention_count, sentiment_trend, recent_mentions), run rollups,
and benchmark joins — all filter/join on these columns, so without these indexes
they degrade to sequential scans as the tables grow.

Revision ID: b2f1c7a4d9e8
Revises: 0963fe96ed39
Create Date: 2026-05-31 17:20:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = "b2f1c7a4d9e8"
down_revision: str | None = "0963fe96ed39"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# (index_name, table, column) — names match the op.f("ix_<table>_<col>") convention
# so they stay consistent with Alembic autogenerate output.
_INDEXES: list[tuple[str, str, str]] = [
    ("ix_companies_primary_ticker_id", "companies", "primary_ticker_id"),
    ("ix_tickers_company_id", "tickers", "company_id"),
    ("ix_aliases_company_id", "aliases", "company_id"),
    ("ix_articles_processing_run_id", "articles", "processing_run_id"),
    ("ix_articles_status", "articles", "status"),
    ("ix_article_companies_article_id", "article_companies", "article_id"),
    ("ix_article_companies_company_id", "article_companies", "company_id"),
    ("ix_article_companies_ticker_id", "article_companies", "ticker_id"),
    ("ix_sentiments_article_id", "sentiments", "article_id"),
    ("ix_sentiments_company_id", "sentiments", "company_id"),
    ("ix_ground_truth_article_id", "ground_truth", "article_id"),
    ("ix_ground_truth_labeled_by", "ground_truth", "labeled_by"),
    ("ix_audit_logs_actor_id", "audit_logs", "actor_id"),
    ("ix_benchmark_results_processing_run_id", "benchmark_results", "processing_run_id"),
]


def upgrade() -> None:
    for name, table, column in _INDEXES:
        op.create_index(name, table, [column], unique=False)


def downgrade() -> None:
    for name, table, _column in reversed(_INDEXES):
        op.drop_index(name, table_name=table)
