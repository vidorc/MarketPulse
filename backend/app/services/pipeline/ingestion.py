"""CSV ingestion: validation, preview, and row extraction.

Validation runs before any processing so the analyst sees row counts, detected
issues, and a preview. Column names are matched flexibly (case/space-insensitive)
against the known MarketPulse / legacy schema.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

# Accepted source column -> canonical field. Keys are normalized (lower, stripped).
_COLUMN_MAP = {
    "title": "title",
    "headline": "title",
    "article_text": "body",
    "article": "body",
    "body": "body",
    "text": "body",
    "description": "description",
    "url": "url",
    "link": "url",
    "source": "source",
    "publisher": "source",
    "date_published": "date_published",
    "published": "date_published",
    "date": "date_published",
}


@dataclass
class CsvRow:
    title: str
    body: str = ""
    url: str | None = None
    source: str | None = None


@dataclass
class CsvValidationReport:
    valid: bool
    total_rows: int
    valid_rows: int
    columns: list[str]
    issues: list[str] = field(default_factory=list)
    preview: list[dict] = field(default_factory=list)


def _norm_key(k: str) -> str:
    return (k or "").strip().lower()


def parse_csv(content: bytes) -> tuple[list[CsvRow], list[str], list[str]]:
    """Parse CSV bytes into rows. Returns (rows, raw_columns, issues)."""
    issues: list[str] = []
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    raw_columns = list(reader.fieldnames or [])

    if not raw_columns:
        return [], [], ["File has no header row or is empty."]

    # Map each raw column to a canonical field, if recognized.
    field_for_col = {col: _COLUMN_MAP.get(_norm_key(col)) for col in raw_columns}
    if "title" not in field_for_col.values():
        issues.append("Required column 'title' (or 'headline') not found.")

    rows: list[CsvRow] = []
    empty_titles = 0
    for raw in reader:
        mapped: dict[str, str] = {}
        for col, value in raw.items():
            target = field_for_col.get(col)
            if target and value is not None:
                # First non-empty wins if multiple columns map to same field.
                if not mapped.get(target):
                    mapped[target] = str(value).strip()
        title = mapped.get("title", "").strip()
        if not title:
            empty_titles += 1
            continue
        rows.append(
            CsvRow(
                title=title,
                body=mapped.get("body", ""),
                url=mapped.get("url") or None,
                source=mapped.get("source") or None,
            )
        )

    if empty_titles:
        issues.append(f"{empty_titles} row(s) skipped due to empty title.")

    return rows, raw_columns, issues


def validate_csv(content: bytes, preview_n: int = 5) -> tuple[CsvValidationReport, list[CsvRow]]:
    rows, columns, issues = parse_csv(content)
    has_title = "title" in {_COLUMN_MAP.get(_norm_key(c)) for c in columns}

    report = CsvValidationReport(
        valid=has_title and len(rows) > 0,
        total_rows=len(rows),
        valid_rows=len(rows),
        columns=columns,
        issues=issues,
        preview=[
            {"title": r.title, "body": r.body[:200], "url": r.url, "source": r.source}
            for r in rows[:preview_n]
        ],
    )
    return report, rows
