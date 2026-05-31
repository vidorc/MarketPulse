# MarketPulse V2 — Design Specification

**Date:** 2026-05-31
**Status:** Approved — full build across all phases
**Author:** Engineering

---

## 1. Summary

MarketPulse is an AI-powered market-intelligence platform. Given a financial news
article it determines the article type, the NSE-listed companies materially discussed,
their tickers, per-company sentiment, an impact level, a confidence score, and the
model's reasoning.

This document specifies the transformation of the existing single-file Python script
(`company_mapper_llm.py`) into a deployment-ready full-stack product: **Next.js 15 +
FastAPI + PostgreSQL + Redis + Celery**, with benchmarking, audit, and analytics
dashboards.

The system is built but not deployed; the architecture must be deployment-ready with
minimal additional work.

### Core contract

Input: an article (`title`, `article_text`).
Output (per article):

```json
{
  "article_type": "company_specific",
  "companies": ["Adani Ports and Special Economic Zone Limited"],
  "tickers": ["ADANIPORTS"],
  "sentiment": "positive",
  "impact": "high",
  "confidence": 94,
  "reasoning": "Explicit Q4 earnings preview for a named company."
}
```

---

## 2. Confirmed decisions

- **LLM provider:** `LLMProvider` abstraction. Default `GroqProvider`
  (`llama-3.1-8b-instant`, already working, free). `MockProvider` for tests.
  Claude/OpenAI providers are swappable via config without touching callers.
- **Build strategy:** vertical slice first (upload → process → view), then expand.
  Each phase is independently runnable and verified before the next begins.
- **Ground truth:** seed `ground_truth` from the existing `mapped_results.csv`
  (~70 labeled rows) and grow it via in-UI analyst labeling/corrections.
- **Tests:** `MockProvider` by default — deterministic, free, CI-safe. Real API
  calls only when `LLM_PROVIDER=groq` and `MARKETPULSE_ALLOW_REAL_LLM=1`.

### Simplicity constraints (explicit lead preference)

Keep the AI layer simple: Article → LLM → Company Mapping → Ticker Mapping → Output.
**Do NOT** introduce vector databases, embeddings, semantic search, multi-stage
validation chains, or agent systems.

---

## 3. Phase decomposition

Each phase is its own spec → plan → implement → verify cycle. The full design below
covers all phases; implementation proceeds phase by phase.

| Phase | Name | Delivers |
|------|------|----------|
| 0 | Foundation | Monorepo, git, Docker Compose (Postgres+Redis), Alembic, config, base FastAPI + Next.js, NSE seeder |
| 1 | Vertical slice | Models, resolution engine, LLM abstraction, pipeline, Celery, CSV upload/validate/preview/process, REST APIs, News Feed + Article Review UI |
| 2 | Auth & RBAC | `users`, JWT, login, Admin/Analyst/Viewer guards, frontend auth |
| 3 | Benchmarking | `ground_truth` + `benchmark_results`, seed, benchmark engine, in-UI labeling, False Positive / False Negative dashboards |
| 4 | Analytics & audit | `audit_logs`, analytics aggregations, Recharts dashboards, Audit / Company Explorer / Settings / main Dashboard pages |

---

## 4. Repository layout

```
MarketPulse/
  backend/
    app/
      core/          # config, security, logging, dependencies
      db/            # session, base; alembic/ for migrations
      models/        # SQLAlchemy ORM, one module per aggregate
      schemas/       # Pydantic DTOs
      repositories/  # data access only, no business logic
      services/
        resolution/  # company resolution / alias engine (ports the script)
        llm/         # LLMProvider ABC, groq.py, mock.py, factory.py
        pipeline/    # orchestration: extract -> resolve -> sentiment -> impact -> persist
        benchmark/   # precision/recall/F1/accuracy engine
        analytics/   # aggregations for dashboards
      api/v1/         # thin routers calling services
      workers/        # celery app + tasks
      storage/        # Storage ABC: local.py now, s3.py later
      seeds/          # nse company seeder, ground-truth bootstrap
    tests/            # unit + integration, mirrors app/
    alembic.ini
    pyproject.toml
  frontend/
    app/              # Next.js 15 app router pages
    components/        # ui (shadcn) + feature components
    lib/               # api client, auth, generated types
  infra/
    docker-compose.yml
    Dockerfile.backend
    Dockerfile.frontend
  docs/
  data/               # gitignored: large CSVs, NSE list, uploads
```

**Git hygiene:** repo is initialized fresh. `.gitignore` excludes `venv/`, large
CSVs (`results_*.csv`, `merged_results.csv`, `market_moving_news.csv`, ~900MB total),
`.env`, `data/`, `node_modules/`, `__pycache__/`.

---

## 5. Data model

Eleven specified tables plus `ground_truth` (required for benchmarking). Normalized.

- **users** — id, email (unique), hashed_password, role (`admin|analyst|viewer`),
  is_active, created_at.
- **companies** — id, canonical_name (unique), primary_ticker_id (FK), created_at.
- **tickers** — id, symbol (unique), company_id (FK), series, isin, face_value.
- **aliases** — id, company_id (FK), alias_text, normalized (indexed), source
  (`generated|acronym|manual`), is_active. Unique on (normalized).
- **articles** — id, title, body, url, source, date_published, content_hash
  (unique, for dedupe), processing_run_id (FK), status
  (`pending|processed|failed`), created_at.
- **article_companies** — id, article_id (FK), company_id (FK), ticker_id (FK),
  alias_used, confidence, is_manual_correction, created_at. The M2M join carrying
  per-link evidence.
- **sentiments** — id, article_id (FK), company_id (FK), label
  (`positive|neutral|negative`), score (nullable float).
- **classifications** — id, article_id (FK, unique), article_type, impact
  (`low|medium|high`), confidence (0–100), reasoning, raw_llm_json.
- **processing_runs** — id, source_filename, total_rows, processed, failed,
  status (`running|completed|failed`), started_at, finished_at.
- **benchmark_results** — id, processing_run_id (FK, nullable), scope
  (`overall|per_category`), category (nullable), precision, recall, f1, accuracy,
  tp, fp, fn, created_at.
- **ground_truth** — id, article_id (FK, nullable), title, expected_tickers
  (csv/json), expected_type, label_source (`seed|analyst`), labeled_by (FK users,
  nullable), created_at.
- **audit_logs** — id, actor_id (FK users, nullable for system), entity_type,
  entity_id, action, before (json), after (json), created_at.

Article types (enum): `company_specific, market_movers, broker_recommendations,
technical_analysis, macro_or_sector, earnings, mergers_and_acquisitions,
regulatory, management_commentary`. The legacy script also emits `multi_company_news`;
it is normalized to `market_movers` on ingest, with the raw value preserved in
`classifications.raw_llm_json`.

---

## 6. Company resolution engine

Ports `build_canonical_registry()` from the script into a DB-backed, analyst-editable
engine.

**Alias generation per company:**
- Exact normalized canonical name and symbol.
- Suffix-stripped name (drop `limited|ltd|corp|corporation|inc|co|company|india|
  industries|industry|services|service|holdings|holding|financial|financials|group|
  energy|power|telecom|technologies|technology`).
- Safe last-word removal: `Ambuja Cements` → `Ambuja`, only when the result is
  ≥4 chars and not in the unsafe set.
- Curated acronym/short-form map (`m&m`, `hul`, `sbi`, `ril`, `tcs`, `infy`, `l&t`,
  `ioc`, `hul`, `au`, `au bank`, `ujjivan`, `ujjivan sfb`, `gillette`, `havells`,
  `ambuja`, etc.).

**Normalization** (`normalize_alias`): lowercase, `&`→`and`, strip non-alphanumerics
to spaces, collapse whitespace.

**Dangerous-alias guard:** `unsafe_shorts = {bank, bank of, state, state bank,
p and g, the, housing, development}` are never registered as aliases, so
`State Bank of India` never resolves on `state` and `Bank of Baroda` never resolves
on `bank`.

**Resolution output:** `resolve(name) -> {company, ticker, alias_used} | None`.
The `alias_used` is surfaced in the audit dashboard. Aliases live in the `aliases`
table (queryable, editable) rather than an in-memory dict, and are (re)built by a
seeder.

---

## 7. LLM extraction engine

`LLMProvider` ABC: `extract(title: str, body: str) -> ExtractionResult`.

`ExtractionResult`: `article_type`, `companies: list[str]`, `confidence: int`,
`reasoning: str`, plus per-company `sentiment` and an article-level `impact`.

- **GroqProvider** — carries the existing system+user prompt verbatim (it already
  encodes the "materially discussed companies" rules, the do-not-return list,
  multi-company support, and few-shot examples), JSON mode, temperature 0,
  retry with exponential backoff. Body truncated to `MAX_CHARS=1200` (inverted
  pyramid). Prompt extended to also request per-company `sentiment` and `impact`.
- **MockProvider** — deterministic fixtures keyed by title substring; returns
  recorded `ExtractionResult`s. Used in all tests by default.
- **factory** — selects provider from `settings.LLM_PROVIDER`.

**Extraction rules** (from the prompt): return companies when earnings, acquisitions,
projects, recommendations, operational/regulatory impact, or market-mover mentions
are present. Never return brokers, analysts, indices, sectors, exchanges, or unnamed
groups. Support multi-company extraction. Strictly-broad technical/macro pieces
return `companies: []`.

**Sentiment** (per company): positive / neutral / negative. **Impact**: low / medium /
high, driven by earnings, acquisition, regulatory event, major project, guidance, or
market movement. **Confidence**: 0–100 from the model.

---

## 8. Processing pipeline

`PipelineService.process_article(title, body, run_id)`:

1. Compute `content_hash`; skip if already processed (idempotent).
2. `llm.extract()` → ExtractionResult.
3. For each company: `resolution.resolve()` → ticker + alias_used; record misses.
4. Persist: `articles`, `classifications`, `article_companies`, `sentiments`.
5. Emit `audit_logs` entry (system actor). Update `processing_runs` counters.

Runs synchronously for small inputs; dispatched to **Celery** (Redis broker) for
large CSVs. Failures are caught per-row, recorded in `processing_runs.failed` and an
audit log, and never abort the run.

---

## 9. News ingestion

CSV upload endpoint: validates schema (requires `title`; `article_text`/`body`,
`url`, `source`, `date_published` optional), returns row count, detected issues
(missing columns, empty titles, duplicates), and a preview (first N rows) **before**
processing. A separate process call enqueues the validated run.

---

## 10. Benchmarking

Ports the script's set-based metric math exactly. Per article, compares predicted
tickers to ground-truth tickers:

- `tp = |pred ∩ true|`, `fp = |pred − true|`, `fn = |true − pred|`.
- `precision = tp/(tp+fp)`, `recall = tp/(tp+fn)`,
  `f1 = 2·p·r/(p+r)`, `accuracy = tp/(tp+fp+fn)`.
- Overall and per-article-type breakdown (`company_specific`, `market_movers`,
  `broker_recommendations`, `technical_analysis`, `macro_or_sector`, …).

Persists to `benchmark_results`. Produces the False-Positive list (articles with
`fp>0`) and False-Negative list (articles with `fn>0`) that drive those dashboards.
Ground truth is seeded from `mapped_results.csv` and grown via analyst labeling.

---

## 11. API design

REST under `/api/v1`:

- `POST /articles/upload` — multipart CSV → validation report + preview.
- `POST /articles/process` — enqueue processing of an uploaded run.
- `GET /articles`, `GET /articles/{id}` — list (filter/paginate) + detail.
- `POST /articles/{id}/corrections` — analyst manual correction.
- `GET /companies`, `GET /companies/{id}` — list + detail (aliases, mentions, trend).
- `GET /analytics` — dashboard aggregations.
- `GET /benchmarks` — latest + historical benchmark results, FP/FN lists.
- `GET /audit` — audit log feed.
- `GET /ground-truth`, `POST /ground-truth` — labels.
- `POST /auth/login`, `POST /auth/register`, `GET /auth/me` — auth.

OpenAPI schema generates the frontend TypeScript client/types.

---

## 12. Security

JWT authentication (access tokens, hashed passwords via passlib/bcrypt). Role-based
access: **Admin** (everything incl. user mgmt, settings), **Analyst** (review,
correct, label, run benchmarks), **Viewer** (read-only). FastAPI dependency guards
enforce per-endpoint roles. Any network-exposed endpoint without auth is flagged;
all data endpoints require a valid token.

---

## 13. Frontend

Next.js 15 (app router), TypeScript, TailwindCSS, shadcn/ui, Recharts. Bloomberg/
terminal aesthetic: dark, dense, monospace numerics. Pages:

- **Dashboard** — totals (articles, companies tagged, avg confidence), precision/
  recall/F1, recent runs, top mentioned/positive/negative companies.
- **News Feed** — paginated, filterable article list.
- **Article Review** — title, body, type, companies, tickers, sentiment, impact,
  confidence, reasoning; manual correction.
- **Company Explorer** — name, ticker, aliases, recent mentions, sentiment trend,
  news timeline, mention frequency.
- **Benchmark Analytics** — precision/recall/F1/accuracy, per-category breakdown,
  trends.
- **Model Performance** — confidence distribution, FP/FN dashboards.
- **Audit Logs** — filterable audit feed; per-article LLM output, mapped company/
  ticker, confidence, reasoning, alias used, errors.
- **Settings** — provider/config, user management (admin).

Charts (Recharts): article-type distribution, sentiment distribution, top mentioned
companies, daily processing volume, confidence distribution, benchmark trends.

---

## 14. Code quality & testing

Modular architecture, type safety (Pydantic + mypy-friendly, TS strict), service
layer + repository pattern, structured logging, explicit error handling.

Tests (run green at the end of every phase):
- **Backend** — pytest, unit per service + integration against a test Postgres.
- **Frontend** — Vitest + Testing Library.
- **Alias resolution** — including the dangerous-alias guards.
- **LLM extraction** — against MockProvider + recorded fixtures.
- **Benchmark** — metric-math correctness.

---

## 15. Local development

`docker compose up` brings up Postgres, Redis, backend (uvicorn), Celery worker, and
frontend. Alembic migrations + seeders run on first boot. `.env.example` documents
all variables. Docs: `README.md`, `docs/SETUP.md`, `docs/DEVELOPMENT.md`.

---

## 16. Out of scope (YAGNI)

Vector DBs, embeddings, semantic search, multi-stage validation chains, agent
systems, live deployment/CD, real-time streaming ingestion, multi-tenancy.
