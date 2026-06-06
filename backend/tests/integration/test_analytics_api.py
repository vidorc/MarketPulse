"""Analytics dashboard + audit feed API.

Verifies the dashboard aggregations reflect actual articles/companies, that the
audit feed is paginated and analyst-gated, and that both endpoints handle an
empty database without erroring.
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def populated(db):
    """A small world: 2 companies, 3 articles with classifications + mentions +
    sentiments, plus a processing run and a couple of audit entries."""
    from app.models.article import (
        Article,
        ArticleCompany,
        Classification,
        Sentiment,
    )
    from app.models.company import Company, Ticker
    from app.models.processing_run import ProcessingRun
    from app.repositories.article_repo import compute_content_hash
    from app.repositories.audit_repo import AuditRepository

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

    tcs, tcs_t = add_company("Tata Consultancy Services", "TCS")
    infy, infy_t = add_company("Infosys", "INFY")

    run = ProcessingRun(source_filename="news.csv", total_rows=3, status="completed")
    db.add(run)
    db.flush()

    def add_article(title, atype, impact, conf, links, sentiment):
        a = Article(
            title=title,
            body="b",
            content_hash=compute_content_hash(title, "b"),
            status="processed",
            processing_run_id=run.id,
        )
        db.add(a)
        db.flush()
        db.add(
            Classification(
                article_id=a.id,
                article_type=atype,
                impact=impact,
                confidence=conf,
            )
        )
        for company, ticker in links:
            db.add(
                ArticleCompany(
                    article_id=a.id,
                    company_id=company.id,
                    ticker_id=ticker.id,
                    confidence=conf,
                )
            )
            db.add(
                Sentiment(
                    article_id=a.id, company_id=company.id, label=sentiment
                )
            )
        db.flush()

    add_article("TCS Q4", "earnings", "high", 95, [(tcs, tcs_t)], "positive")
    add_article("Infy guidance", "earnings", "medium", 80, [(infy, infy_t)], "negative")
    add_article(
        "IT majors rally",
        "market_movers",
        "medium",
        70,
        [(tcs, tcs_t), (infy, infy_t)],
        "positive",
    )

    AuditRepository(db).log(action="article_corrected", entity_type="article", entity_id=1)
    AuditRepository(db).log(action="benchmark.run", entity_type="benchmark")
    db.commit()
    return {"run_id": run.id}


class TestAnalytics:
    def test_overview_totals(self, client, populated):
        res = client.get("/api/v1/analytics")
        assert res.status_code == 200
        body = res.json()
        assert body["total_articles"] == 3
        assert body["processed_articles"] == 3
        assert body["total_companies"] == 2
        assert body["companies_tagged"] == 2
        assert body["total_runs"] == 1

    def test_avg_confidence(self, client, populated):
        body = client.get("/api/v1/analytics").json()
        # (95 + 80 + 70) / 3 = 81.67
        assert abs(body["avg_confidence"] - 81.7) < 0.1

    def test_article_type_distribution(self, client, populated):
        body = client.get("/api/v1/analytics").json()
        types = {d["label"]: d["count"] for d in body["article_types"]}
        assert types["earnings"] == 2
        assert types["market_movers"] == 1

    def test_top_companies_ranked_by_mentions(self, client, populated):
        body = client.get("/api/v1/analytics").json()
        top = body["top_companies"]
        # TCS appears in 2 articles, Infy in 2 — both have 2 mentions.
        assert {c["ticker"] for c in top} == {"TCS", "INFY"}
        assert all(c["mentions"] == 2 for c in top)

    def test_sentiment_distribution(self, client, populated):
        body = client.get("/api/v1/analytics").json()
        sent = {d["label"]: d["count"] for d in body["sentiment_distribution"]}
        # positive: TCS Q4 + both in rally = 3 ; negative: Infy guidance = 1
        assert sent["positive"] == 3
        assert sent["negative"] == 1

    def test_confidence_buckets_present(self, client, populated):
        body = client.get("/api/v1/analytics").json()
        labels = [b["label"] for b in body["confidence_buckets"]]
        assert labels == ["0-20", "20-40", "40-60", "60-80", "80-100"]

    def test_empty_db_returns_zeros(self, client):
        body = client.get("/api/v1/analytics").json()
        assert body["total_articles"] == 0
        assert body["avg_confidence"] == 0.0

    def test_requires_auth(self, raw_client):
        assert raw_client.get("/api/v1/analytics").status_code == 401


class TestAuditFeed:
    def test_lists_recent_entries(self, client, populated):
        res = client.get("/api/v1/audit")
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 2
        actions = {e["action"] for e in body["items"]}
        assert actions == {"article_corrected", "benchmark.run"}

    def test_filter_by_action(self, client, populated):
        body = client.get("/api/v1/audit?action=benchmark.run").json()
        assert body["total"] == 1
        assert body["items"][0]["action"] == "benchmark.run"

    def test_filter_by_entity_type(self, client, populated):
        body = client.get("/api/v1/audit?entity_type=article").json()
        assert body["total"] == 1
        assert body["items"][0]["entity_type"] == "article"

    def test_viewer_cannot_read_audit(self, raw_client, populated, make_user, auth_header):
        viewer = make_user(email="v-audit@test.io", role="viewer")
        res = raw_client.get("/api/v1/audit", headers=auth_header(viewer))
        assert res.status_code == 403

    def test_unauthenticated_is_401(self, raw_client):
        assert raw_client.get("/api/v1/audit").status_code == 401
