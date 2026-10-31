# KG-ResearchAI Backend REST Service

FastAPI Backend API for the **LLM + Knowledge Graph Research Assistant with Hybrid RAG**.

For full project overview and frontend documentation, please see the [Root README](file:///d:/FY/README.md).

---

## 🛠️ Technology Stack

- **Python**: `>= 3.11`
- **Package & Environment Manager**: `uv`
- **Framework**: FastAPI + Uvicorn + Pydantic v2
- **Databases**:
  - PostgreSQL + `pgvector` (Vector Storage & Relational Data via SQLAlchemy Async)
  - Neo4j (Knowledge Graph Storage & Cypher queries via Neo4j Python Driver)
  - Redis (Caching & Job Queue)
- **AI & ML**: Groq Cloud (`openai/gpt-oss-120b`, Llama 3.3) / Google Gemini / Ollama, SentenceTransformers (`all-MiniLM-L6-v2`), PyTorch GCN (GNN Link Prediction)

---

## 🚀 Quick Setup & Execution

### 1. Prerequisites & Environment Setup

Ensure Python 3.11+, `uv`, and Docker Desktop are installed. Ensure `.env` is configured with your database and LLM credentials:

```powershell
# Copy environment template if not already present
cp .env.example .env
```

### 2. Start Database Stack (Docker Compose)

```powershell
docker-compose up -d postgres neo4j redis
```

### 3. Virtual Environment & Dependencies

```powershell
# Create virtual environment
uv venv

# Activate (Windows PowerShell)
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

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
├── tests/               # Pytest automated test suite
├── Dockerfile.backend   # Backend Docker container definition
├── docker-compose.yml   # Multi-service database & web compose setup
├── pyproject.toml       # Package dependencies
├── requirements.txt     # Python requirements
├── run_all.ps1 / .bat   # Full-stack launcher scripts
└── stop_all.ps1 / .bat  # Full-stack shutdown scripts
```
