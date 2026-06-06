"""Benchmark metric math — verified against hand-computed expectations.

These pin the set-based scoring ported from the legacy script: tp = |pred ∩ true|,
fp = |pred − true|, fn = |true − pred|, summed across articles, then
precision/recall/F1/accuracy derived. A regression here silently misreports model
quality, so the math is tested directly and independently of the DB.
"""
from __future__ import annotations

import math

from app.services.benchmark.engine import (
    Counts,
    EvalItem,
    compute_benchmark,
    normalize_ticker_set,
    score_one,
)


class TestNormalizeTickerSet:
    def test_splits_and_uppercases(self):
        assert normalize_ticker_set("tcs, infy") == {"TCS", "INFY"}

    def test_handles_pipe_separator(self):
        assert normalize_ticker_set("TCS|INFY") == {"TCS", "INFY"}

    def test_drops_empty_and_nan(self):
        assert normalize_ticker_set("TCS,, nan ,") == {"TCS"}

    def test_none_is_empty(self):
        assert normalize_ticker_set(None) == set()


class TestScoreOne:
    def test_perfect_match(self):
        c = score_one({"TCS", "INFY"}, {"TCS", "INFY"})
        assert (c.tp, c.fp, c.fn) == (2, 0, 0)

    def test_partial_with_extra_and_missing(self):
        # predicted {A,B}, expected {B,C}: tp=B, fp=A, fn=C
        c = score_one({"A", "B"}, {"B", "C"})
        assert (c.tp, c.fp, c.fn) == (1, 1, 1)

    def test_empty_prediction_against_truth(self):
        c = score_one(set(), {"X", "Y"})
        assert (c.tp, c.fp, c.fn) == (0, 0, 2)

    def test_both_empty_is_all_zero(self):
        c = score_one(set(), set())
        assert (c.tp, c.fp, c.fn) == (0, 0, 0)


class TestCountsMetrics:
    def test_precision_recall_f1_accuracy(self):
        c = Counts(tp=8, fp=2, fn=2)
        assert math.isclose(c.precision, 0.8)
        assert math.isclose(c.recall, 0.8)
        assert math.isclose(c.f1, 0.8)
        # accuracy = tp / (tp+fp+fn) = 8/12
        assert math.isclose(c.accuracy, 8 / 12)

    def test_zero_denominators_are_zero_not_nan(self):
        c = Counts(0, 0, 0)
        assert c.precision == 0.0
        assert c.recall == 0.0
        assert c.f1 == 0.0
        assert c.accuracy == 0.0

    def test_addition_accumulates(self):
        total = Counts(1, 2, 3) + Counts(4, 5, 6)
        assert (total.tp, total.fp, total.fn) == (5, 7, 9)


class TestComputeBenchmark:
    def test_overall_aggregation_and_fp_fn_lists(self):
        items = [
            EvalItem("a", {"TCS"}, {"TCS"}, category="company_specific"),
            EvalItem("b", {"INFY", "WIPRO"}, {"INFY"}, category="company_specific"),
            EvalItem("c", set(), {"SBI"}, category="earnings"),
        ]
        report = compute_benchmark(items)
        # tp: a=1, b=1, c=0 => 2 ; fp: b has WIPRO => 1 ; fn: c missing SBI => 1
        assert (report.overall.tp, report.overall.fp, report.overall.fn) == (2, 1, 1)
        assert report.evaluated == 3
        # b produced a false positive, c a false negative.
        fp_titles = {f.title for f in report.false_positives}
        fn_titles = {f.title for f in report.false_negatives}
        assert fp_titles == {"b"}
        assert fn_titles == {"c"}

    def test_per_category_breakdown(self):
        items = [
            EvalItem("a", {"TCS"}, {"TCS"}, category="company_specific"),
            EvalItem("b", {"INFY", "WIPRO"}, {"INFY"}, category="company_specific"),
            EvalItem("c", set(), {"SBI"}, category="earnings"),
        ]
        report = compute_benchmark(items)
        cats = {m.category: m for m in report.per_category}
        assert cats["company_specific"].rows == 2
        assert (cats["company_specific"].counts.tp, cats["company_specific"].counts.fp) == (2, 1)
        assert cats["earnings"].counts.fn == 1

    def test_empty_input(self):
        report = compute_benchmark([])
        assert report.evaluated == 0
        assert report.overall.f1 == 0.0
        assert report.per_category == []
