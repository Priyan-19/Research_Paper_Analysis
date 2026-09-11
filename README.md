# 🧠 LLM + Knowledge Graph Research Assistant

> **A Hybrid RAG Platform combining Vector Search, Knowledge Graphs, and Large Language Models for Grounded Academic & Research Intelligence.**

---

## 📋 Overview

The **LLM + Knowledge Graph Research Assistant** is an advanced AI research platform engineered to process, index, and reason over collections of academic research papers (PDFs).

Traditional PDF chatbots rely exclusively on dense vector similarity, which struggles with complex relationship reasoning across multiple papers (e.g., comparing methods, tracking citation networks, or identifying co-authorship). This system resolves those limitations by pairing **Vector Embeddings (PostgreSQL + pgvector)** with a structured **Knowledge Graph (Neo4j)**, orchestrated via a **Hybrid RAG Pipeline** powered by Large Language Models (Gemini / Ollama / OpenAI / Claude).

---

## ✨ Key Features

- 📄 **Research PDF Ingestion & Semantic Chunking**: Automated extraction of text, sections, and metadata (authors, publication year, venue, abstract, citations) from academic papers.
- 🕸️ **Automated Knowledge Graph Construction**: Uses LLMs to extract entities (Papers, Authors, Concepts, Methods, Datasets, Models) and canonicalized relationships into Neo4j.
- 🔍 **Hybrid Retrieval Engine (Vector + Graph)**:
  - **Vector Search**: PostgreSQL + `pgvector` for semantic similarity retrieval.
  - **Graph Search**: Cypher queries over Neo4j for multi-hop structural reasoning.
  - **Reciprocal Rank Fusion (RRF)**: Merges and ranks vector and graph contexts seamlessly.
- 💬 **Grounded RAG Question Answering**: Synthesizes verified answers with explicit paper & entity citations, eliminating hallucinations.
- 📊 **Interactive Streamlit Dashboard**: A feature-rich UI for paper management, RAG chat, graph visualizers, entity canonicalization, and link prediction.
- ⚡ **FastAPI REST Backend**: Asynchronous microservice API providing Swagger UI documentation (`/docs`) and background worker processing.
- 📈 **Graph Neural Network (GNN) Link Prediction**: Predicts potential future research collaboration and concept connections.

---

## 🛠️ Architecture & Tech Stack

```text
               +----------------------------------+
               |   Streamlit UI / REST Client     |
               +-----------------+----------------+
                                 |
                                 v
               +-----------------+----------------+
               |     FastAPI Backend Service      |
               +-----------------+----------------+
                                 |
        +------------------------+------------------------+
        |                        |                        |
        v                        v                        v
+---------------+        +---------------+        +---------------+
|  PostgreSQL   |        |     Neo4j     |        |     Redis     |
|  + pgvector   |        |  Graph DB     |        | Cache & Queue |
| (Vector Search|        |(Knowledge Graph|        |               |
+---------------+        +---------------+        +---------------+
```

- **Programming Language**: Python >= 3.11
- **Package Manager**: `uv` (Fast Python package installer and resolver)
- **Backend Framework**: FastAPI + Uvicorn + Pydantic v2
- **Vector Database**: PostgreSQL with `pgvector` (via SQLAlchemy Async)
- **Graph Database**: Neo4j (via Neo4j Python Driver & Cypher)
- **Caching & Job Queue**: Redis
- **Frontend Interface**: Streamlit with Plotly graph visualizers
- **LLM & Embeddings**: Google Gemini, Sentence Transformers (`all-MiniLM-L6-v2`), Ollama, or OpenAI

---

## 📁 Repository Structure

```text
.
├── PRD_LLM_Knowledge_Graph_Research_Assistant.md  # Detailed Product Requirements Document
├── modules.md                                      # Architectural Modules Blueprint
├── README.md                                       # Project Overview & Setup Guide
├── .gitignore                                      # Root Git ignore rules
└── backend/                                        # FastAPI Application & Streamlit UI
    ├── app/                                        # Core application package
    │   ├── api/                                    # REST API endpoints (v1)
    │   ├── core/                                   # Application configuration & logging
    │   ├── database/                               # Postgres, Neo4j, and Redis async clients
    │   ├── graph/                                  # Graph extractors, canonicalizer & GNN
    │   ├── ingestion/                              # PDF loader, chunker & metadata extractor
    │   ├── rag/                                    # Hybrid retriever & grounded chat service
    │   ├── schemas/                                # Pydantic data schemas
    │   ├── services/                               # Business logic & paper management
    │   └── workers/                                # Background paper processing workers
    ├── data/                                       # Storage for PDF uploads & processed files
    │   ├── uploads/
    │   └── processed/
    ├── scripts/                                    # Utility scripts (reprocessing, stats, clear DB)
    ├── tests/                                      # Pytest suite
    ├── Dockerfile.backend                          # Backend container definition
    ├── docker-compose.yml                          # Multi-container database setup
    ├── pyproject.toml / requirements.txt           # Python dependency specifications
    ├── run_all.ps1 / run_all.bat                   # Automation scripts to launch full stack
    ├── stop_all.ps1                                # Script to stop running background services
    └── streamlit_app.py                            # Streamlit web application frontend
```

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python**: `>= 3.11`
- **uv**: Python package manager (Recommended) — [Installation Guide](https://github.com/astral-sh/uv)
- **Docker Desktop**: Required to run PostgreSQL (`pgvector`), Neo4j, and Redis databases.

---

### Step 1: Environment Setup

Clone the repository and create your environment configuration file:

```bash
# Navigate to the backend directory
cd backend

# Copy the template environment file
cp .env.example .env
```

Open `.env` and set your API keys (e.g. `GEMINI_API_KEY`) and database configuration as required:

```env
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

### Step 2: Start Database Infrastructure (Docker)

Spin up PostgreSQL with `pgvector`, Neo4j, and Redis using Docker Compose:

```bash
# From the backend directory
docker-compose up -d postgres neo4j redis
```

This starts:
- **PostgreSQL (`pgvector`)**: `localhost:5432`
- **Neo4j Graph Database**: `localhost:7687` (HTTP Browser: `http://localhost:7474`)
- **Redis**: `localhost:6379`

---

### Step 3: Install Dependencies

Using `uv` (Recommended):

```powershell
# Create virtual environment
uv venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\activate

# Install all required packages
uv pip install -r requirements.txt
```

---

### Step 4: Run the Application

#### Option A: One-Click Script (Recommended for Windows)

Run the automated launcher script to start Docker databases, the FastAPI server, and the Streamlit UI simultaneously:

```powershell
# Run via PowerShell
.\run_all.ps1
```

To stop all services when done:
```powershell
.\stop_all.ps1
```

#### Option B: Manual Execution

1. **Start FastAPI Backend**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

2. **Start Streamlit Dashboard**:
   ```bash
   streamlit run streamlit_app.py --server.port 8501
   ```

---

## 🔗 Access Points & Documentation

| Service / Interface | URL | Description |
| :--- | :--- | :--- |
| **Streamlit Web UI** | `http://localhost:8501` | Main interactive research assistant dashboard |
| **FastAPI Swagger Docs** | `http://localhost:8000/docs` | Interactive OpenAPI documentation |
| **FastAPI ReDoc** | `http://localhost:8000/redoc` | Alternative API documentation |
| **API Health Check** | `http://localhost:8000/api/v1/health` | Service health status endpoint |
| **Neo4j Browser UI** | `http://localhost:7474` | Cypher query console (User: `neo4j`, Password: `password`) |

---

## 📜 Utility Scripts

Utility scripts are located in `backend/scripts/`:

- **Check Database Statistics**:
  ```bash
  python scripts/check_stats.py
  ```
- **Reprocess All Uploaded Papers**:
  ```bash
  python scripts/reprocess_all_papers.py
  ```
- **Clear Neo4j Knowledge Graph**:
  ```bash
  python scripts/clear_neo4j.py
  ```

---

## 📄 Documentation References

For full architectural blueprints, entity-relationship schemas, and functional specifications, refer to:
- [PRD Documentation](file:///d:/FY/PRD_LLM_Knowledge_Graph_Research_Assistant.md)
- [Module Blueprint](file:///d:/FY/modules.md)

---

## 📄 License

This project is developed as part of a Final-Year Research Project in Generative AI & Knowledge Graphs.
