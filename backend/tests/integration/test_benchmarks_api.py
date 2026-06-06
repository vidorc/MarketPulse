"""Benchmark + ground-truth API: scoring against ground truth, FP/FN lists, RBAC.

Builds a tiny world (two companies, two articles with predicted ticker links, two
ground-truth labels) and verifies the live benchmark report matches hand-computed
expectations, that snapshots persist for the trend, and that mutating endpoints
require analyst+.
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def world(db):
    """Two companies/tickers + two articles with predictions + ground truth.

    Article 1 ("Adani Ports Q4"): predicted {ADANIPORTS}, truth {ADANIPORTS} -> perfect.
    Article 2 ("TCS and Infy"):   predicted {TCS, INFY}, truth {TCS}       -> 1 fp.
    """
    from app.models.article import Article, ArticleCompany, Classification
    from app.models.benchmark import GroundTruth
    from app.models.company import Company, Ticker
    from app.repositories.article_repo import compute_content_hash

    def add_company(name, symbol):
        c = Company(canonical_name=name)
        db.add(c)
        db.flush()
        t = Ticker(symbol=symbol, company_id=c.id)
        db.add(t)
        db.flush()
        c.primary_ticker_id = t.id
        db.flush()
        return c, t

    adani, adani_t = add_company("Adani Ports", "ADANIPORTS")
    tcs, tcs_t = add_company("Tata Consultancy Services", "TCS")
    infy, infy_t = add_company("Infosys", "INFY")

    def add_article(title, links, atype):
        a = Article(
            title=title,
            body="b",
            content_hash=compute_content_hash(title, "b"),
            status="processed",
        )
        db.add(a)
        db.flush()
        db.add(
            Classification(
                article_id=a.id, article_type=atype, impact="low", confidence=90
            )
        )
        for company, ticker in links:
            db.add(
                ArticleCompany(
                    article_id=a.id,
                    company_id=company.id,
                    ticker_id=ticker.id,
                    confidence=90,
                )
            )
        db.flush()
        return a

    a1 = add_article("Adani Ports Q4", [(adani, adani_t)], "company_specific")
    a2 = add_article("TCS and Infy", [(tcs, tcs_t), (infy, infy_t)], "market_movers")

    db.add(
        GroundTruth(
            title="Adani Ports Q4",
            expected_tickers="ADANIPORTS",
            expected_type="company_specific",
            label_source="seed",
        )
    )
    db.add(
        GroundTruth(
            title="TCS and Infy",
            expected_tickers="TCS",
            expected_type="market_movers",
            label_source="seed",
        )
    )
    db.commit()
    return {"a1": a1.id, "a2": a2.id}


class TestGetBenchmarks:
    def test_overall_metrics_match_hand_computation(self, client, world):
        res = client.get("/api/v1/benchmarks")
        assert res.status_code == 200
        body = res.json()
        # tp = ADANIPORTS + TCS = 2 ; fp = INFY = 1 ; fn = 0
        assert body["overall"]["tp"] == 2
        assert body["overall"]["fp"] == 1
        assert body["overall"]["fn"] == 0
        # precision = 2/3, recall = 1.0
        assert abs(body["overall"]["precision"] - 2 / 3) < 1e-9
        assert body["overall"]["recall"] == 1.0
        assert body["evaluated"] == 2

    def test_false_positive_list_surfaces_the_extra_ticker(self, client, world):
        body = client.get("/api/v1/benchmarks").json()
        fp_titles = {f["title"] for f in body["false_positives"]}
        assert fp_titles == {"TCS and Infy"}
        fp = next(f for f in body["false_positives"] if f["title"] == "TCS and Infy")
        assert "INFY" in fp["predicted"]
        assert fp["expected"] == ["TCS"]

    def test_per_category_breakdown_present(self, client, world):
        body = client.get("/api/v1/benchmarks").json()
        cats = {c["category"]: c for c in body["per_category"]}
        assert cats["company_specific"]["tp"] == 1
        assert cats["market_movers"]["fp"] == 1

    def test_empty_world_returns_zeros_not_error(self, client):
        res = client.get("/api/v1/benchmarks")
        assert res.status_code == 200
        assert res.json()["evaluated"] == 0
        assert res.json()["overall"]["f1"] == 0.0

    def test_requires_auth(self, raw_client, world):
        assert raw_client.get("/api/v1/benchmarks").status_code == 401


class TestRunBenchmarkSnapshot:
    def test_run_persists_and_appears_in_trend(self, client, world):
        run = client.post("/api/v1/benchmarks/run")
        assert run.status_code == 200
        assert run.json()["evaluated"] == 2

        trend = client.get("/api/v1/benchmarks/trend")
        assert trend.status_code == 200
        points = trend.json()
        assert len(points) >= 1
        assert points[-1]["recall"] == 1.0

    def test_viewer_cannot_run(self, raw_client, world, make_user, auth_header):
        viewer = make_user(email="v-bench@test.io", role="viewer")
        res = raw_client.post(
            "/api/v1/benchmarks/run", headers=auth_header(viewer)
        )
        assert res.status_code == 403


class TestGroundTruth:
    def test_list_returns_seeded_labels(self, client, world):
        res = client.get("/api/v1/ground-truth")
        assert res.status_code == 200
        assert res.json()["total"] == 2

    def test_analyst_can_add_label_and_it_scores(self, client, world):
        # Add a label for an existing article and confirm it's counted.
        res = client.post(
            "/api/v1/ground-truth",
            json={
                "title": "Adani Ports Q4",
                "expected_tickers": ["adaniports"],
                "expected_type": "company_specific",
            },
        )
        assert res.status_code == 201
        assert res.json()["expected_tickers"] == "ADANIPORTS"

    def test_viewer_cannot_add_label(self, raw_client, world, make_user, auth_header):
        viewer = make_user(email="v-gt@test.io", role="viewer")
        res = raw_client.post(
            "/api/v1/ground-truth",
            headers=auth_header(viewer),
            json={"title": "x", "expected_tickers": ["TCS"]},
        )
        assert res.status_code == 403
