<div align="center">

# 📈 MarketPulse

**AI-Powered Financial Market Intelligence Platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js_15-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Groq](https://img.shields.io/badge/Groq_LLM-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/)

**Extract. Analyze. Benchmark. Make smarter investment decisions with real-time market insights.**

<img src="./assets/marketpulse-banner.png" alt="MarketPulse Dashboard Banner" width="100%" />

</div>

---

## 📖 Overview

**MarketPulse** is a full-stack financial market intelligence platform built for investors, financial analysts, and quantitative researchers. It ingests financial news, processes unstructured content using large language models, and converts it into structured signals such as company mentions, sentiment, and estimated market impact.

The platform also includes a built-in evaluation pipeline, making it possible to benchmark extraction quality over time using Precision, Recall, and F1 score against human-verified ground truth datasets.

***

## ✨ Key Features

- 🤖 **Automated News Processing Pipeline** — Ingests financial articles and processes them asynchronously.
- 📊 **LLM-Based Entity Resolution** — Extracts company mentions, maps them to known tickers, and classifies impact.
- 📈 **Sentiment Analysis** — Tracks positive, negative, and neutral sentiment across selected equities.
- 🏢 **Company Explorer** — Lets users inspect company-specific mention history and related market-moving news.
- ⏱️ **Analytics Dashboard** — Summarizes intelligence, platform activity, and system health in one place.
- 🎯 **Benchmarking Suite** — Measures Precision, Recall, and F1 score to monitor model quality.
- 📝 **Audit Logs & Human Review** — Supports corrections, traceability, and ground truth management.
- 🔐 **Authentication & RBAC** — Secures access with user authentication and role-based permissions.

***

## 🏗️ Architecture

MarketPulse follows a decoupled, service-oriented architecture designed to handle expensive AI workloads through asynchronous processing.

```mermaid
graph TD

    subgraph Frontend["Frontend - Next.js 15"]
        UI["User Interface"]
        Pages["Dashboards & Views"]
        UI --> Pages
    end

    subgraph Backend["Backend - FastAPI"]
        API["REST API"]
        Auth["Authentication"]
        Routes["API Routes"]

        API --> Auth
        API --> Routes
    end

    subgraph Workers["Asynchronous Processing"]
        Broker["Redis Message Broker"]
        Celery["Celery Workers"]
        LLM["Groq LLM / AI Inference"]

        Broker --> Celery
        Celery --> LLM
    end

    subgraph Data["Data Persistence"]
        DB[("PostgreSQL")]
        Cache[("Redis Cache")]
    end

    Pages -->|HTTP/REST| API

    Routes -->|Read/Write| DB
    Routes -->|Queue Task| Broker
    Routes -->|Cache Operations| Cache

    Celery -->|Fetch/Store| DB
    Celery -->|Inference Request| LLM
```

### 💻 Tech Stack

| Category | Technologies |
|----------|--------------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, React Query |
| Backend | FastAPI, Python 3.12+, Pydantic, SQLAlchemy, Alembic |
| Database & Cache | PostgreSQL, Redis |
| Task Queue | Celery |
| AI & ML | Groq LLM API, Prompt Engineering, Zero-Shot/Few-Shot Classification |
| Infrastructure | Docker, Docker Compose (planned) |

***

## 📂 Repository Structure

```text
MarketPulse/
├── assets/                 # Static assets and repository visuals
│   └── marketpulse-banner.png
├── backend/                # FastAPI backend service
│   ├── alembic/            # Database migrations
│   ├── app/
│   │   ├── api/            # Route handlers
│   │   ├── core/           # Settings, auth, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic and LLM integration
│   │   └── worker/         # Celery task definitions
│   ├── data/               # Seed files and CSVs
│   ├── tests/              # Pytest test suite
│   ├── .env.example        # Environment template
│   └── pyproject.toml      # Python dependencies
├── docs/                   # Extended project documentation
├── frontend/               # Next.js frontend app
│   ├── src/                # Frontend source code
│   ├── public/             # Public assets
│   ├── package.json        # Node dependencies
│   └── tailwind.config.ts  # Tailwind configuration
└── infra/                  # Infrastructure configs
```

***

## 🔌 API Endpoints Overview

The backend exposes a documented OpenAPI interface. The core route groups are listed below.

| Module | Route Prefix | Description |
|--------|--------------|-------------|
| Authentication | `/api/v1/auth` | Login, registration, password reset |
| Articles | `/api/v1/articles` | Ingest articles, query processed data, upload CSV batches |
| Companies | `/api/v1/companies` | Company CRUD and ticker resolution |
| Analytics | `/api/v1/analytics` | Aggregated dashboard metrics |
| Benchmarks | `/api/v1/benchmarks` | Run evaluations and fetch Precision, Recall, and F1 |
| Ground Truth | `/api/v1/ground-truth` | Manage verified benchmark datasets |
| Audit Logs | `/api/v1/audit` | Track corrections and system actions |

***

## 🚀 Getting Started

### Prerequisites

- Node.js 20+ with npm or pnpm
- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- Groq API key

### 1. Clone the Repository

```bash
git clone https://github.com/vidorc/MarketPulse.git
cd MarketPulse
```

### 2. Configure Environment Variables

**Backend (`backend/.env`)**

```env
DATABASE_URL=postgresql://user:password@localhost:5432/marketpulse
REDIS_URL=redis://localhost:6379/0
GROQ_API_KEY=gsk_your_groq_api_key_here
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Frontend (`frontend/.env.local`)**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
# or: poetry install
```

Run migrations:

```bash
alembic upgrade head
```

Start the API server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Start the Celery worker in a new terminal:

```bash
cd backend
source venv/bin/activate
celery -A app.worker.celery_app worker --loglevel=info
```

### 4. Frontend Setup

```bash
cd frontend
npm install
# or
pnpm install
```

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

***

## 📊 Evaluation & Benchmarking

MarketPulse includes a dedicated benchmarking workflow to evaluate the reliability of its LLM extraction pipeline against human-annotated ground truth data.

### Benchmark Flow

1. Open the **Benchmarks** section in the UI.
2. Select a target ground truth dataset.
3. Dispatch asynchronous re-evaluation tasks through Celery.
4. Review updated Precision, Recall, and F1 score results on the performance dashboard.

This makes it easier to detect prompt drift, regression, or extraction quality changes over time.

***

## 🛣️ Future Roadmap

- [ ] Dockerization with a complete `docker-compose.yml`
- [ ] Real-time WebSocket updates for live extraction results
- [ ] Multi-LLM support with fallback providers
- [ ] Advanced graph visualizations for company relationships
- [ ] RSS-based or automated news source ingestion

***

## 🧠 Learning Outcomes

Building MarketPulse demonstrates practical experience in:

- **System Design** — Architecting asynchronous workflows around Redis and Celery.
- **AI Engineering** — Designing prompts, structured extraction flows, and LLM evaluation loops.
- **Full-Stack Development** — Integrating a Next.js frontend with a FastAPI backend and relational database.
- **Data Quality Workflows** — Applying ML-style evaluation metrics inside generative AI systems.

***

## 👨‍💻 Author

Built with ❤️ by **Mayank Sharma**

- GitHub: [@vidorc](https://github.com/vidorc)
- LinkedIn: [Mayank Sharma](https://www.linkedin.com/in/mayank-sharma1832/)
- Portfolio: [mayanks-portfolio.vercel.app](https://mayanks-portfolio.vercel.app/)

***

## ⭐ Support

If you found this project useful, consider starring the repository. It helps more people discover the project and supports future development.
