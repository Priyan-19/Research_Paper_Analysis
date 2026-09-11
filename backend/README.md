# KG-ResearchAI Backend & Streamlit Web UI

FastAPI Backend & Streamlit Interactive UI for the **LLM + Knowledge Graph Research Assistant with Hybrid RAG**.

For full project overview and documentation, please see the [Root README](file:///d:/FY/README.md).

---

## 🛠️ Technology Stack

- **Python**: `>= 3.11`
- **Package & Environment Manager**: `uv`
- **Framework**: FastAPI + Uvicorn + Pydantic v2
- **Databases**:
  - PostgreSQL + `pgvector` (Vector Storage & Relational Data)
  - Neo4j (Knowledge Graph Storage & Cypher queries)
  - Redis (Caching & Task Queue)
- **Frontend UI**: Streamlit + Plotly
- **AI & ML**: Google Gemini / OpenAI / Ollama, SentenceTransformers (`all-MiniLM-L6-v2`), PyTorch Geometric (GNN Link Prediction)

---

## 🚀 Quick Setup & Execution

### 1. Prerequisites & Environment Setup

Ensure `uv` and Docker Desktop are installed. Copy `.env.example` to `.env`:

```powershell
cp .env.example .env
```

Ensure your `GEMINI_API_KEY` (or chosen LLM credentials) is configured inside `.env`.

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

### Automated Launch (Powershell / Windows)

Run both the FastAPI backend server and Streamlit frontend UI simultaneously:

```powershell
.\run_all.ps1
```

To stop background processes:
```powershell
.\stop_all.ps1
```

### Manual Service Launch

1. **FastAPI REST API Backend** (Port 8000):
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. **Streamlit Web UI** (Port 8501):
   ```powershell
   streamlit run streamlit_app.py --server.port 8501
   ```

---

## 🔗 Key Endpoints & Dashboards

- **Streamlit Web Dashboard**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check API**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Neo4j Cypher Browser**: [http://localhost:7474](http://localhost:7474)

---

## 📂 Backend Architecture

```text
backend/
├── app/
│   ├── api/v1/          # REST API endpoints (health, papers, chat, graph)
│   ├── core/            # App settings (Pydantic), logging, exceptions
│   ├── database/        # Async drivers for PostgreSQL, Neo4j, Redis
│   ├── graph/           # Entity canonicalization, relationship extractor, GNN
│   ├── ingestion/       # PyMuPDF parser, semantic chunker, metadata extractor
│   ├── rag/             # Vector, Graph & Hybrid retrievers, grounded chat
│   ├── schemas/         # Request/Response Pydantic schemas
│   ├── services/        # Paper management & business logic
│   └── workers/         # Async paper processing pipeline
├── data/
│   ├── uploads/         # Staging area for raw PDF uploads
│   └── processed/       # Extracted JSON & processed chunks
├── scripts/             # Admin scripts (check_stats.py, reprocess_all_papers.py, clear_neo4j.py)
├── tests/               # Pytest automated test suite
├── Dockerfile.backend   # Backend Docker build definition
├── docker-compose.yml   # Postgres + pgvector, Neo4j, Redis setup
├── pyproject.toml       # Package dependencies
├── requirements.txt     # Locked dependencies
├── run_all.ps1          # Automated full-stack starter script
├── stop_all.ps1         # System cleanup script
└── streamlit_app.py     # Streamlit multi-tab Web Dashboard
```
