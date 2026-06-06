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

**MarketPulse** is a comprehensive, production-ready full-stack financial intelligence platform designed for investors, financial analysts, and quantitative researchers. It automatically ingests financial news, processes unstructured data using advanced Large Language Models (LLMs), and extracts actionable insights such as company mentions, sentiment analysis, and market impact classifications. 

Built with scalability and precision in mind, MarketPulse not only provides a powerful analytics dashboard but also features a built-in benchmarking system to continuously evaluate the underlying AI model's Precision, Recall, and F1 scores against human-verified ground truth data.

---

## ✨ Key Features

* 🤖 **AI-Powered News Processing Pipeline:** Automated ingestion and asynchronous processing of financial news and articles.
* 📊 **LLM Entity Resolution & Impact Classification:** Utilizes Groq LLMs to accurately extract company mentions, map them to known tickers, and classify market impact.
* 📈 **Real-Time Sentiment Analysis:** Track positive, negative, and neutral sentiments across targeted equities.
* 🏢 **Company Explorer:** Deep-dive into specific companies to trace historical mentions and news-driven market movement.
* ⏱️ **Analytics Dashboard:** A beautiful, responsive interface summarizing key financial metrics, recent intelligence, and system health.
* 🎯 **Evaluation & Benchmarking:** A robust system tracking model Precision, Recall, and F1 metrics to ensure reliable AI extractions over time.
* 📝 **Audit Logs & Human-in-the-Loop Corrections:** Tools for data quality assurance, allowing experts to correct model outputs and manage ground truth datasets.
* 🔐 **Secure Access:** Comprehensive User Authentication with Role-Based Access Control (RBAC).

---

## 🏗️ Architecture

MarketPulse follows a decoupled microservices-inspired architecture, leveraging asynchronous task queues for heavy LLM workloads.

```mermaid
graph TD
    subgraph Frontend [Frontend - Next.js 15]
        UI[User Interface]
        Pages[Dashboards & Views]
        UI --> Pages
    end

    subgraph Backend [Backend - FastAPI]
        API[RESTful API]
        Auth[Authentication]
        Routes[API Routes]
        API --> Auth
        API --> Routes
    end

    subgraph Workers [Asynchronous Processing]
        Broker[Redis Message Broker]
        Celery[Celery Workers]
        LLM[Groq LLM / AI Inference]
    end

    subgraph Data [Data Persistence]
        DB[(PostgreSQL)]
        Cache[(Redis Cache)]
    end

    Pages -- HTTP/REST --> API
    Routes -- Read/Write --> DB
    Routes -- Queue Task --> Broker
    Broker --> Celery
    Celery -- Fetch/Store --> DB
    Celery -- Inference --> LLM
    Routes -- Cache --> Cache
💻 Tech StackCategoryTechnologiesFrontendNext.js 15, TypeScript, Tailwind CSS, shadcn/ui, React QueryBackendFastAPI, Python 3.12+, Pydantic, SQLAlchemy, AlembicDatabase & CachePostgreSQL, RedisTask QueueCeleryAI & MLGroq LLM API, Prompt Engineering, Zero-Shot/Few-Shot ClassificationInfrastructureDocker, Docker Compose (Planned)📂 Repository StructurePlaintextMarketPulse/
├── assets/                 # Static assets and repository imagery
│   └── marketpulse-banner.png
├── backend/                # FastAPI application backend
│   ├── alembic/            # Database migrations
│   ├── app/                # Application source code
│   │   ├── api/            # Route handlers
│   │   ├── core/           # Config and security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic validation models
│   │   ├── services/       # Business logic & LLM integration
│   │   └── worker/         # Celery task definitions
│   ├── data/               # Seed data & CSVs
│   ├── tests/              # Pytest test suite
│   ├── .env.example        # Environment variables template
│   └── pyproject.toml      # Python dependencies
├── docs/                   # Extended documentation
├── frontend/               # Next.js 15 application
│   ├── src/                # Frontend source code
│   ├── public/             # Public assets
│   ├── package.json        # Node.js dependencies
│   └── tailwind.config.ts  # Tailwind CSS configuration
└── infra/                  # Infrastructure configurations
🔌 API Endpoints OverviewThe backend exposes a fully documented OpenAPI (Swagger) interface. Here are the core module routes:ModuleRoute PrefixDescriptionAuthentication/api/v1/authJWT Login, Registration, Password ResetArticles/api/v1/articlesIngest news, query processed articles, upload CSV batchesCompanies/api/v1/companiesCRUD for company entities and ticker resolutionAnalytics/api/v1/analyticsAggregated metrics for dashboardsBenchmarks/api/v1/benchmarksRun evaluations and fetch Precision/Recall/F1 scoresGround Truth/api/v1/ground-truthManage verified datasets for model testingAudit Logs/api/v1/auditTrack human corrections and system actions🚀 Getting StartedPrerequisitesNode.js 20+ & npm/pnpmPython 3.12+PostgreSQL 15+Redis 7+Groq API Key1. Clone the RepositoryBashgit clone [https://github.com/yourusername/MarketPulse.git](https://github.com/yourusername/MarketPulse.git)
cd MarketPulse
2. Environment VariablesBackend (backend/.env):Code snippetDATABASE_URL=postgresql://user:password@localhost:5432/marketpulse
REDIS_URL=redis://localhost:6379/0
GROQ_API_KEY=gsk_your_groq_api_key_here
SECRET_KEY=your_super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
Frontend (frontend/.env.local):Code snippetNEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
3. Backend Setup & ExecutionNavigate to the backend directory and install dependencies:Bashcd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt # Or poetry install if using Poetry
Run Database Migrations:Bashalembic upgrade head
Start the FastAPI Server:Bashuvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Start the Celery Worker (In a new terminal):Bashcd backend
source venv/bin/activate
celery -A app.worker.celery_app worker --loglevel=info
4. Frontend Setup & ExecutionNavigate to the frontend directory:Bashcd frontend
npm install
# or
pnpm install
Start the Next.js Development Server:Bashnpm run dev
Open http://localhost:3000 in your browser.📊 Evaluation & BenchmarkingMarketPulse includes a dedicated benchmarking suite to evaluate the reliability of the Groq LLM prompts against human-annotated Ground Truth data.To run a benchmark pipeline:Navigate to the Benchmarks tab in the UI.Select a target Ground Truth dataset.The system dispatches asynchronous tasks via Celery to re-evaluate articles.View updated Precision, Recall, and F1 Scores on the Model Performance dashboard to detect prompt drift or degradation.🛣️ Future Roadmap[ ] Dockerization: Complete docker-compose.yml for one-click deployments.[ ] Real-time WebSockets: Push live news extraction results to the frontend.[ ] Multi-LLM Support: Add fallback support for OpenAI GPT-4o and Anthropic Claude 3.5 Sonnet.[ ] Advanced Graphing: Implement interactive D3.js / Recharts network graphs for company relationships.[ ] Automated Web Scraping: Direct RSS feed integration for continuous news ingestion.🧠 Learning OutcomesBuilding MarketPulse demonstrates expertise in:System Architecture: Designing decoupled applications using message brokers (Redis/Celery) to handle rate-limited external AI APIs.AI Engineering: Applying applied prompt engineering, entity resolution, and deterministic JSON extraction from stochastic LLMs.Full-Stack Development: Connecting modern React ecosystems (Next.js 15) with robust Python backends (FastAPI/SQLAlchemy).Data Quality Engineering: Implementing evaluation metrics (F1, Precision, Recall) traditionally used in ML into generative AI workflows.👨‍💻 AuthorBuilt with ❤️ by [Your Name/Handle]GitHub: @YourUsernameLinkedIn: Your NamePortfolio: yourwebsite.com⭐ Show your supportIf you found this project interesting or helpful, please consider leaving a Star ⭐️! It helps others discover the repository and motivates further open-source contributions.