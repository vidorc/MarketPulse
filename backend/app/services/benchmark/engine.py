"""Benchmark metric engine — pure, set-based ticker scoring.

Ports the metric math from the legacy ``company_mapper_llm.py`` exactly: for each
article we compare the *set* of predicted tickers to the *set* of ground-truth
tickers, accumulate true/false positives and false negatives, and derive
precision / recall / F1 / accuracy. Kept free of any DB or I/O so it is trivially
unit-testable against hand-computed expectations.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


def normalize_ticker_set(raw: str | None) -> set[str]:
    """Parse a comma/pipe-separated ticker string into an uppercased set.

    Mirrors the legacy parsing: split on ``,`` (and ``|``), trim, uppercase, and
    drop empties and the literal string ``nan`` (pandas-serialized missing value).
    """
    if not raw:
        return set()
    cleaned = str(raw).replace("|", ",")
    return {
        t.strip().upper()
        for t in cleaned.split(",")
        if t.strip() and t.strip().lower() != "nan"
    }


@dataclass(frozen=True)
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(self.tp + other.tp, self.fp + other.fp, self.fn + other.fn)

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 0.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def accuracy(self) -> float:
        # Jaccard-style: correct over the union of predicted and expected.
        d = self.tp + self.fp + self.fn
        return self.tp / d if d else 0.0


def score_one(predicted: set[str], expected: set[str]) -> Counts:
    """Set-based scoring for a single article."""
    return Counts(
        tp=len(predicted & expected),
        fp=len(predicted - expected),
        fn=len(expected - predicted),
    )


@dataclass
class EvalItem:
    """One predicted-vs-expected pair to score."""

    title: str
    predicted: set[str]
    expected: set[str]
    category: str | None = None  # ground-truth article type, for per-category rollup
    article_id: int | None = None


@dataclass
class CategoryMetrics:
    category: str
    counts: Counts
    rows: int


@dataclass
class FalseItem:
    title: str
    predicted: list[str]
    expected: list[str]
    article_id: int | None = None


@dataclass
class BenchmarkReport:
    overall: Counts
    per_category: list[CategoryMetrics] = field(default_factory=list)
    false_positives: list[FalseItem] = field(default_factory=list)
    false_negatives: list[FalseItem] = field(default_factory=list)
    evaluated: int = 0


def compute_benchmark(items: list[EvalItem]) -> BenchmarkReport:
    """Aggregate per-article counts into overall + per-category metrics, and
    collect the false-positive / false-negative articles for the dashboards."""
    overall = Counts()
    by_cat: dict[str, Counts] = defaultdict(Counts)
    cat_rows: dict[str, int] = defaultdict(int)
    fps: list[FalseItem] = []
    fns: list[FalseItem] = []

    for item in items:
        c = score_one(item.predicted, item.expected)
        overall = overall + c
        cat = item.category or "uncategorized"
        by_cat[cat] = by_cat[cat] + c
        cat_rows[cat] += 1

        if c.fp > 0:
            fps.append(
                FalseItem(
                    title=item.title,
                    predicted=sorted(item.predicted),
                    expected=sorted(item.expected),
                    article_id=item.article_id,
                )
            )
        if c.fn > 0:
            fns.append(
                FalseItem(
                    title=item.title,
                    predicted=sorted(item.predicted),
                    expected=sorted(item.expected),
                    article_id=item.article_id,
                )
            )

    per_category = [
        CategoryMetrics(category=cat, counts=by_cat[cat], rows=cat_rows[cat])
        for cat in sorted(by_cat)
    ]
    return BenchmarkReport(
        overall=overall,
        per_category=per_category,
        false_positives=fps,
        false_negatives=fns,
        evaluated=len(items),
    )
