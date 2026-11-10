# KG-ResearchAI Backend REST Service

FastAPI Backend API for the **LLM + Knowledge Graph Research Assistant with Hybrid RAG**.

For full project overview and frontend documentation, please see the [Root README](file:///d:/FY/README.md).

---

## 🛠️ Technology Stack

- **Python**: `>= 3.11` (Runtime: Python 3.12 / Container: `python:3.11-slim`)
- **Package & Environment Manager**: `uv` / `pip`
- **Framework**: FastAPI + Uvicorn + Pydantic v2
- **Databases**:
  - PostgreSQL 16 + `pgvector` (Vector Storage & Relational Data via SQLAlchemy 2.0 Async)
  - Neo4j 5 Community (Knowledge Graph Storage & Cypher queries with APOC)
  - Redis 7 (Caching & Background Task Queue)
- **AI & ML**: Groq Cloud (`openai/gpt-oss-120b`, Llama 3.3) / Google Gemini / Ollama, SentenceTransformers (`all-MiniLM-L6-v2`), PyTorch GCN (GNN Link Prediction)
- **Testing & Quality**: `pytest 9+`, `pytest-cov`, `pytest-asyncio`, `ruff`, `bandit`, `pip-audit`

---

## 🚀 Quick Setup & Execution

### 1. Prerequisites & Environment Setup

Ensure Python 3.11+, `uv` (or `pip`), and Docker Desktop are installed. Ensure `.env` is configured with your database and LLM credentials:

```powershell
# Copy environment template if not already present
cp .env.example .env
```

### 2. Start Database Stack (Docker Compose)

```powershell
docker-compose up -d postgres neo4j redis
```

All three services feature automated healthchecks:
- **PostgreSQL**: `pg_isready -U postgres`
- **Neo4j**: `wget --spider http://localhost:7474`
- **Redis**: `redis-cli ping`

### 3. Virtual Environment & Dependencies

```powershell
# Create virtual environment
uv venv

# Activate (Windows PowerShell)
.venv\Scripts\activate
# Or Linux / macOS: source .venv/bin/activate

# Install pinned dependencies
uv pip install -r requirements.txt
```

---

## 🧪 Testing, Quality Assurance & Coverage

The backend is backed by an automated test suite across unit, API, and multi-database integration levels.

### Test Metrics

- **Total Test Cases**: **105 tests**
- **Test Pass Rate**: **100% (105/105 passed)**
- **Overall Line Coverage**: **73.0%** (Exceeds 65% minimum gate)
- **Execution Time**: ~6.1 seconds

### Running Tests Locally

```powershell
# 1. Run all unit, API, and integration tests with detailed terminal coverage:
.venv\Scripts\python.exe -m pytest tests --cov=app --cov-report=term-missing

# 2. Run tests enforcing the 65% minimum coverage threshold:
.venv\Scripts\python.exe -m pytest tests --cov=app --cov-fail-under=65

# 3. Run unit tests only:
.venv\Scripts\python.exe -m pytest tests/unit -v

# 4. Run API route tests only:
.venv\Scripts\python.exe -m pytest tests/api -v

# 5. Run integration pipeline tests:
.venv\Scripts\python.exe -m pytest tests/integration -v
```

### Test Architecture

- **`tests/conftest.py`**: Disables blocking network lifespan hooks on `FastAPI` during tests (`_noop_lifespan`), intercepts and mocks external LLM provider calls with `guard_external_llm`, and provides reusable database mocks.
- **`tests/unit/`**: Isolated unit tests for:
  - Claim-level verification & grounding (`test_claim_verification.py`)
  - Multi-tenancy & access control (`test_multi_tenancy_security.py`)
  - Full-paper chunk-based graph extraction (`test_full_paper_extractor.py`)
  - Hybrid entity canonicalization & version protection (`test_hybrid_canonicalizer.py`, `test_canonicalizer.py`)
  - PyTorch GNN training pipeline & negative sampling (`test_gnn_training.py`)
  - Tri-Hybrid RRF retrieval & reranker fallback (`test_tri_hybrid_rag.py`)
  - Layout-aware PDF & table parsing (`test_pdf_loader.py`)
  - Section detection (`test_section_detector.py`)
  - Semantic chunking (`test_chunker.py`)
  - Dense embeddings (`test_embeddings.py`)
  - Cypher query builder (`test_neo4j_builder.py`)
  - Vector similarity store (`test_vector_store.py`)
  - Citation guardrail (`test_citation_guard.py`)
- **`tests/api/`**: TestClient verification for health endpoints (`test_health_api.py`) and paper upload/listing endpoints (`test_papers_api.py`).
- **`tests/integration/`**: Component interaction tests verifying PDF parser to chunker, chunker to embedding vectors, and RRF retrieval mechanics (`test_pipeline_integration.py`).

For full technical specifications and migration details, refer to:
- [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)
- [`docs/DATABASE_MIGRATIONS.md`](../docs/DATABASE_MIGRATIONS.md)
- [`docs/TESTING_REPORT.md`](../docs/TESTING_REPORT.md)
- [`docs/KNOWN_LIMITATIONS.md`](../docs/KNOWN_LIMITATIONS.md)

---

## 🎯 Running the Services

### Automated Launch (One Command)

From the project root (`D:\FY`) or `backend`:

```powershell
.\run_all.ps1
```
*(Or in CMD: `run_all.bat`)*

To stop all services:
```powershell
.\stop_all.ps1
```
*(Or in CMD: `stop_all.bat`)*

### Manual Backend Launch

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 🔗 Key Endpoints & Dashboards

- **FastAPI Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check API**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Neo4j Cypher Browser**: [http://localhost:7474](http://localhost:7474)
- **React Frontend Web UI**: [http://localhost:5173](http://localhost:5173)

---

## 🔄 Automated CI/CD Workflows

Backend changes are validated by GitHub Actions workflows in `.github/workflows/`:

- **`backend-ci.yml`**: Runs on push/PR for `backend/**`. Executes Ruff linting, sets up Python 3.12, runs 105 tests, validates coverage (`--cov-fail-under=65`), and archives `coverage.xml`.
- **`integration-tests.yml`**: Spins up live Docker service containers (`pgvector`, `neo4j`, `redis`) and executes multi-database integration tests.
- **`security-checks.yml`**: Scans dependencies with `pip-audit` for CVEs and executes Bandit SAST code security checks.
- **`docker-build.yml`**: Validates containerization using `Dockerfile.backend` with multi-stage Buildx caching.

---

## 📂 Backend Architecture

```text
backend/
├── app/
│   ├── api/v1/          # REST API endpoints (health, papers, chat, graph, analysis, evaluation)
│   ├── core/            # App settings (Pydantic), logging, custom exceptions
│   ├── database/        # Async clients for PostgreSQL, Neo4j, Redis
│   ├── embeddings/      # Vector store & sentence embedding service
│   ├── graph/           # Entity canonicalization, relationship extractor, GNN link predictor
│   ├── ingestion/       # PyMuPDF parser, semantic chunker, metadata extractor
│   ├── llm/             # Multi-provider LLM abstraction layer (Groq, Gemini, Llama)
│   ├── rag/             # Vector, Graph & Hybrid retrievers (RRF), grounded chat service
│   ├── schemas/         # Request/Response Pydantic v2 data models
│   ├── services/        # Paper management & business logic
│   └── workers/         # Async paper processing pipeline
├── data/
│   ├── uploads/         # Staging area for raw PDF uploads
│   └── processed/       # Extracted JSON & processed chunks
├── scripts/             # Admin & evaluation scripts (evaluate_rag.py, check_stats.py, etc.)
├── tests/               # Pytest automated test suite (105 tests, 73.0% coverage)
│   ├── conftest.py      # Lifespan overrides, LLM guardrails, DB fixtures
│   ├── api/             # Health & Papers TestClient tests
│   ├── integration/     # Pipeline interaction tests
│   └── unit/            # Isolated component unit tests
├── Dockerfile.backend   # Backend Docker container definition (Python 3.11-slim)
├── docker-compose.yml   # Multi-service database & web compose setup with healthchecks
├── pyproject.toml       # Package dependencies (PEP 518)
├── requirements.txt     # Pinned Python requirements
├── run_all.ps1 / .bat   # Full-stack launcher scripts
└── stop_all.ps1 / .bat  # Full-stack shutdown scripts
```

---

<div align="center">

Built with 🌿 for Academic Research Intelligence

Developed by **[Priyan-19](https://github.com/Priyan-19)**

© 2026 Academic Research Intelligence System. All Rights Reserved.

</div>
