<div align="center">

# 🧠 LLM + Knowledge Graph Research Assistant
### Hybrid RAG Intelligence Platform for Academic & Scientific Research Papers 🌐📚

[![Vite](https://img.shields.io/badge/VITE-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![React](https://img.shields.io/badge/REACT%2018-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TYPESCRIPT-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TAILWIND%20CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/FASTAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/PYTHON%203.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/GOOGLE%20GEMINI-8E75C2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Groq Cloud](https://img.shields.io/badge/GROQ%20CLOUD-F55036?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com/)
[![PostgreSQL](https://img.shields.io/badge/POSTGRESQL%20PGVECTOR-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Neo4j](https://img.shields.io/badge/NEO4J%20GRAPH-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com/)
[![Redis](https://img.shields.io/badge/REDIS-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![PyTorch](https://img.shields.io/badge/PYTORCH%20GNN-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)

**LLM + Knowledge Graph Research Assistant** is a state-of-the-art hybrid AI intelligence platform engineered to index, cross-reference, reason over, and synthesize complex academic research papers (PDFs). By orchestrating dense vector similarity search with structured graph relational traversal and Graph Neural Networks, it delivers verifiable, hallucination-free research synthesis with precise citations.

</div>

---

## 📖 Project Overview

Traditional PDF chatbots and standard RAG systems rely exclusively on dense vector embeddings. While vector search excels at finding isolated passages with semantic similarities, it fails systematically when asked to:
1. Reason across multiple interrelated papers (e.g., comparing methodologies or identifying common benchmarks).
2. Trace structural citation genealogies and academic co-authorship networks.
3. Discover non-obvious, unasserted research links across distinct domains.

This platform resolves those structural limitations through a **Tri-Layer Hybrid Retrieval-Augmented Generation (Hybrid RAG)** architecture. It unifies **PostgreSQL + `pgvector`** (for dense semantic retrieval), **Neo4j** (for structured multi-hop graph querying), **Reciprocal Rank Fusion (RRF)**, and **PyTorch Graph Convolutional Networks (GCN)**, driven by high-throughput LLM reasoning via Groq Cloud (`openai/gpt-oss-120b` / `llama-3.3-70b-versatile`) and Google Gemini.

### Core Value Proposition
- **🛡️ Grounded & Hallucination-Free**: Every claim is strictly backed by verifiable paper and page citations `[Paper, Page X]`.
- **🕸️ Dual-Engine Hybrid Retrieval**: Parallel vector similarity + Cypher multi-hop graph traversal unified via Reciprocal Rank Fusion.
- **📈 Predictive Scientific Discovery**: Built-in Graph Neural Network (GNN) link prediction uncovers unasserted research connections.
- **⚡ High-Throughput Streaming Backend**: Asynchronous FastAPI microservice with real-time Server-Sent Events (SSE) streaming.
- **📰 Editorial Production Web UI**: Modern, responsive React 18 + Vite interface crafted with an academic typography and canvas-based graph visualizer.
- **🌐 End-to-End Orchestration**: Ingestion → Entity Extraction → Graph Canonicalization → Hybrid RAG → Visual Synthesis.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Presentation Layer ["1. Presentation Layer (Port 5173)"]
        UI["React 18 + Vite + TypeScript Dashboard"]
        ChatUI["Typewriter Streaming Chat (SSE)"]
        GraphViz["Interactive Knowledge Graph (react-force-graph-2d)"]
        GNNUI["GNN Link Prediction & Canonicalization UI"]
        Katex["KaTeX Math & Highlight.js Engine"]
    end

    subgraph API Gateway ["2. Backend Microservice Layer (Port 8000)"]
        FastAPI["FastAPI REST API (/api/v1)"]
        Uvicorn["Uvicorn ASGI Server"]
        AsyncORM["SQLAlchemy 2.0 Async + asyncpg"]
        Validation["Pydantic v2 Data Schemas & Settings"]
    end

    subgraph Ingestion Engine ["3. Document Processing Pipeline"]
        PyMuPDF["PyMuPDF (fitz) Layout-Aware Parser"]
        Chunker["Semantic Section Chunker & Metadata Extractor"]
        Embedder["Sentence Transformers (all-MiniLM-L6-v2, 384-dim)"]
    end

    subgraph AI Framework ["4. Hybrid RAG & Intelligence Core"]
        LLM["Groq Cloud (openai/gpt-oss-120b / Llama 3.3)"]
        RRF["Reciprocal Rank Fusion Engine (RRF Rank = Σ 1 / (60 + r))"]
        GNN["GNN Link Predictor (PyTorch GCN)"]
        Canon["Entity Canonicalizer & Deduplicator"]
        Guard["Citation & Grounding Guardrail"]
    end

    subgraph Storage Layer ["5. Database Infrastructure"]
        PG[("PostgreSQL + pgvector (Port 5432)")]
        NEO[("Neo4j Graph Database (Port 7687 / 7474)")]
        REDIS[("Redis Cache & Task Queue (Port 6379)")]
    end

    UI --> FastAPI
    ChatUI --> FastAPI
    GraphViz --> FastAPI
    GNNUI --> FastAPI
    FastAPI --> PyMuPDF
    PyMuPDF --> Chunker --> Embedder
    Embedder --> PG
    Chunker --> Canon --> NEO
    FastAPI --> RRF
    RRF --> PG
    RRF --> NEO
    RRF --> GNN
    RRF --> LLM
    LLM --> Guard --> ChatUI
    FastAPI --> REDIS
```
---

## 🚀 Key Features

### 📄 Academic PDF Ingestion & Semantic Chunking
- **Layout-Aware Extraction**: Powered by PyMuPDF (`fitz`), automatically preserving academic structure, abstracts, multi-column text, sections, and references.
- **Dense Vector Embedding**: Embeds passages into 384-dimensional dense vectors using `sentence-transformers/all-MiniLM-L6-v2`.
- **HNSW Indexing**: High-performance approximate nearest neighbor search via `pgvector` with cosine similarity ranking.

### 🕸️ Automated Knowledge Graph Construction
- **Autonomous Entity Extraction**: Automatically identifies and categorizes domain entities:
  - `Paper`, `Author`, `Concept`, `Method`, `Dataset`, `Model`, `Metric`.
- **Relational Edge Mapping**: Populates typed relational edges:
  - `AUTHORED_BY`, `PROPOSES`, `USES_METHOD`, `EVALUATED_ON`, `CITES`, `EXTENDS`.
- **Automated Canonicalization**: Merges synonym variations (e.g., *"CNN"*, *"ConvNet"*, *"Convolutional Neural Network"*) to ensure graph integrity.

### 🔍 Dual-Engine Hybrid Retrieval (RRF)
- **Vector Search**: PostgreSQL `pgvector` retrieves contextually similar passages using Cosine Distance.
- **Graph Traversal**: Cypher queries navigate 2-3 hop relational neighborhoods in Neo4j to find structural dependencies.
- **Reciprocal Rank Fusion**: Merges both score distributions dynamically using the standard RRF formula:
  $$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{60 + r_m(d)}$$

### 💬 Grounded Question Answering & Citation Guardrails
- **Anti-Hallucination Pipeline**: The LLM context is strictly bound to retrieved evidence chunks and graph triples.
- **Verifiable In-Text Citations**: Automatically appends verifiable references `[Paper Name, Page X]` to statements.
- **Typewriter SSE Streaming**: Smooth token-by-token response generation with interactive side-panel evidence cards.

### 📈 Graph Neural Network (GNN) Link Prediction
- **PyTorch Geometric GCN**: Analyzes topological graph neighborhoods to predict latent connections between concepts, emerging methods, and authors.
- **Collaborative Research Discovery**: Suggests novel research pairings and cross-disciplinary citation potentials.

### 🎨 Modern Editorial React Dashboard
- **Editorial Typography & Aesthetics**: Newsreader serif headings, warm parchment background (`#fef9f0`), monospaced metadata, and clean card containers.
- **Interactive 2D Force-Directed Graph**: Real-time canvas exploration of nodes and relationships via `react-force-graph-2d`.
- **LaTeX Math & Syntax Highlighting**: Math equations rendered via KaTeX (`$E=mc^2$`), code snippets formatted with Highlight.js.
- **Zero Mock Data**: Production mode strictly connected to live backend databases without pre-fillers or dummy artifacts.

---

## 🛠️ Technology Stack

| Layer | Technologies | Role & Purpose |
| :--- | :--- | :--- |
| **Frontend Framework** | React 18, Vite 5, TypeScript 5.5 | Reactive, typed single-page application |
| **Styling & UI** | Tailwind CSS 3.4, Radix UI, Lucide Icons | Editorial research design system tokens |
| **Graph Visualizer** | `react-force-graph-2d`, HTML5 Canvas | Dynamic interactive knowledge graph exploration |
| **Math & Code Rendering**| KaTeX, `remark-math`, `rehype-highlight` | Academic formula and code block rendering |
| **State Management** | Zustand, TanStack Query (React Query) | Client-side store, server cache & request deduplication |
| **Backend Framework** | FastAPI 0.110+, Uvicorn (ASGI) | Asynchronous REST API microservice (`/api/v1`) |
| **Database ORM** | SQLAlchemy 2.0 (Async), `asyncpg` | Asynchronous PostgreSQL database driver |
| **Data Validation** | Pydantic v2, Pydantic Settings | Strict typing, schema serialization, env validation |
| **Vector Database** | PostgreSQL 16 + `pgvector` | Dense vector storage, cosine distance, HNSW indexing |
| **Graph Database** | Neo4j 5 Community Edition, Cypher | Graph property model, multi-hop relationship queries |
| **In-Memory Cache** | Redis 7 | Query response caching and asynchronous task queuing |
| **LLM Inference** | Groq Cloud (`openai/gpt-oss-120b`, Llama 3.3) | Ultra-fast token generation & reasoning |
| **Alternative LLMs** | Google Gemini (`gemini-1.5-flash`), Ollama | Cloud and local fallback language models |
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2` | 384-dimensional dense semantic representations |
| **PDF Processing** | PyMuPDF (`fitz`) | High-fidelity text, layout, and metadata extraction |
| **Graph Neural Network** | PyTorch, PyTorch Geometric (GCN) | Unsupervised and supervised link prediction |
| **Testing Frameworks** | `pytest`, `pytest-asyncio`, `vitest`, RTL | End-to-end backend (32 tests) & frontend (7 tests) suites |

---

## 📂 Project Structure

```text
d:/FY/
├── backend/                                        # FastAPI REST Application Service
│   ├── app/                                        # Core application package
│   │   ├── api/v1/                                 # API endpoints (health, papers, chat, graph)
│   │   │   ├── chat.py                             # Grounded chat & streaming endpoint
│   │   │   ├── graph.py                            # Graph query, stats & GNN inference
│   │   │   ├── health.py                           # System & database health checks
│   │   │   └── papers.py                           # PDF upload, listing & processing
│   │   ├── core/                                   # Application configuration & logging
│   │   │   ├── config.py                           # Pydantic v2 settings loader
│   │   │   └── logging.py                          # Structured logger setup
│   │   ├── database/                               # Database connectors & clients
│   │   │   ├── neo4j.py                            # Neo4j async session manager
│   │   │   ├── postgres.py                         # SQLAlchemy async engine & session
│   │   │   └── redis.py                            # Redis cache & queue client
│   │   ├── graph/                                  # Knowledge graph modules
│   │   │   ├── canonicalizer.py                    # Entity deduplication & merging
│   │   │   ├── extractor.py                        # LLM entity & relation extractor
│   │   │   └── gnn.py                              # PyTorch GCN link prediction engine
│   │   ├── ingestion/                              # Document ingestion pipeline
│   │   │   ├── chunker.py                          # Layout-aware semantic chunker
│   │   │   ├── embedder.py                         # SentenceTransformers vector generator
│   │   │   └── pdf_loader.py                       # PyMuPDF (fitz) text & metadata reader
│   │   ├── llm/                                    # Multi-provider LLM abstraction
│   │   │   ├── client.py                           # Base LLM client interface
│   │   │   ├── gemini.py                           # Google Gemini API adapter
│   │   │   └── groq.py                             # Groq Cloud API adapter
│   │   ├── rag/                                    # Hybrid RAG reasoning core
│   │   │   ├── guardrail.py                        # Grounding & citation validator
│   │   │   ├── pipeline.py                         # Grounded question-answering orchestrator
│   │   │   └── retriever.py                        # Dual vector + graph retriever with RRF
│   │   ├── schemas/                                # Pydantic data schemas
│   │   │   ├── chat.py                             # Query & response models
│   │   │   ├── graph.py                            # Node, edge & GNN models
│   │   │   └── paper.py                            # Paper metadata & chunk models
│   │   ├── services/                               # Application business logic
│   │   │   └── paper_service.py                    # File handling & ingestion service
│   │   ├── workers/                                # Asynchronous task workers
│   │   │   └── paper_worker.py                     # Background ingestion task processor
│   │   └── main.py                                 # FastAPI application entrypoint
│   ├── data/                                       # Storage for uploads & processed files
│   │   ├── uploads/                                # Raw uploaded PDF documents
│   │   └── processed/                              # Extracted text & chunk artifacts
│   ├── scripts/                                    # Maintenance & administrative scripts
│   │   ├── check_stats.py                          # Check DB records, vectors, and triples
│   │   ├── clear_neo4j.py                          # Safe reset for Neo4j database
│   │   └── reprocess_all_papers.py                 # Batch re-index and re-chunk tool
│   ├── tests/                                      # Pytest unit & integration test suite (32 tests)
│   ├── Dockerfile.backend                          # Production container configuration
│   ├── docker-compose.yml                          # PostgreSQL (pgvector), Neo4j, Redis containers
│   ├── pyproject.toml                              # Python project dependencies (PEP 518)
│   └── requirements.txt                            # Pinned Python package dependencies
│
├── frontend/                                       # React 18 + Vite Modern Web UI
│   ├── src/
│   │   ├── api/                                    # Typed backend client & SSE consumer
│   │   ├── components/                             # Reusable editorial UI components
│   │   │   ├── Chat/                               # Message bubbles, sources panel, composer
│   │   │   ├── Graph/                              # ForceGraph2D canvas & node details
│   │   │   └── Layout/                             # Navigation header & status pills
│   │   ├── pages/                                  # Route pages
│   │   │   ├── ChatPage.tsx                        # Main grounded research chat interface
│   │   │   ├── PapersPage.tsx                      # PDF upload & ingestion management
│   │   │   ├── KnowledgeGraphPage.tsx              # Interactive graph exploration
│   │   │   ├── GNNPredictionPage.tsx               # GNN link prediction & canonicalization
│   │   │   └── EvaluationPage.tsx                  # Empirical benchmarks & retrieval stats
│   │   ├── store/                                  # Zustand global application state
│   │   ├── types/                                  # TypeScript interface declarations
│   │   ├── App.tsx                                 # Root application component
│   │   └── main.tsx                                # React DOM mounting & providers
│   ├── index.html                                  # Web entry point
│   ├── package.json                                # Frontend dependencies & Vitest runner
│   ├── tailwind.config.js                          # Editorial design system token configuration
│   └── vite.config.ts                              # Vite dev server & proxy settings
│
├── System_Architecture.png                         # Ultra-HD system architecture diagram (PNG)
├── System_Architecture.jpg                         # High-res system architecture diagram (JPG)
├── System_Architecture.svg                         # Vector system architecture diagram (SVG)
├── run_all.ps1 / run_all.bat                       # One-command full-stack launchers (Root)
├── stop_all.ps1 / stop_all.bat                     # One-command full-stack shutdown scripts (Root)
├── PRD_LLM_Knowledge_Graph_Research_Assistant.md   # Product Requirements Document
├── modules.md                                      # Architectural Modules Technical Blueprint
├── .gitignore                                      # Comprehensive Git exclusion rules
└── README.md                                       # Master Project Documentation
```

---

## 🚀 Getting Started

### Prerequisites
- **Python**: `3.11` or higher installed
- **Node.js**: `v18.0.0` or higher & `npm`
- **Docker Desktop**: Required to run PostgreSQL (`pgvector`), Neo4j, and Redis
- **uv**: (Recommended) Ultra-fast Python package installer

---

### 1. Clone Repository & Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-username/academic-hybrid-rag.git
cd academic-hybrid-rag
```

Configure backend environment variables:
```bash
cd backend
cp .env.example .env
```

Open `backend/.env` and configure your API keys and credentials:
```env
# Server Configuration
HOST=127.0.0.1
PORT=8000
ENVIRONMENT=development

# LLM Engine Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Database Connections
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/research_rag
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
REDIS_URL=redis://localhost:6379/0
```

---

### 2. Start Database Infrastructure (Docker)

Spin up PostgreSQL (`pgvector`), Neo4j, and Redis with Docker Compose:

```bash
# From the backend directory
docker-compose up -d postgres neo4j redis
```

Verify that all three database containers are healthy:
```bash
docker-compose ps
```

---

### 3. Setup & Launch Backend (FastAPI)

```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies (using uv or pip)
pip install -r requirements.txt

# Start FastAPI development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend will be live at **http://127.0.0.1:8000** with interactive Swagger documentation at **http://127.0.0.1:8000/docs**.

---

### 4. Setup & Launch Frontend (React + Vite)

```bash
# In a new terminal, navigate to frontend
cd frontend

# Copy environment variables
cp .env.example .env

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```

Frontend will be accessible at **http://localhost:5173**.

---

### 5. Automated One-Command Launchers (Windows)

To start all services (Docker databases, FastAPI backend, and React frontend) simultaneously with a single command:

**Using PowerShell:**
```powershell
.\run_all.ps1
```

**Using Command Prompt (CMD):**
```cmd
run_all.bat
```

To gracefully shut down all running services when done:
```powershell
.\stop_all.ps1
```
*(Or in CMD: `stop_all.bat`)*

---

## 🔑 Default Credentials & Access Points

| Service / Interface | URL | Access / Default Credentials | Purpose |
| :--- | :--- | :--- | :--- |
| **React Web Dashboard** | `http://localhost:5173` | Direct Browser Access | Primary research assistant user interface |
| **FastAPI Swagger UI** | `http://localhost:8000/docs` | Public API Documentation | Interactive REST API testing and exploration |
| **FastAPI ReDoc** | `http://localhost:8000/redoc` | Public API Documentation | Formal API technical specification |
| **Backend Health Check** | `http://localhost:8000/api/v1/health` | HTTP GET | Real-time DB and service connectivity check |
| **Neo4j Browser Console**| `http://localhost:7474` | User: `neo4j` \| Password: `password` | Visual Cypher query exploration and graph inspection |
| **PostgreSQL (pgvector)**| `localhost:5432` | User: `postgres` \| Password: `postgres` | Relational metadata and vector embeddings |
| **Redis Cache** | `localhost:6379` | Default No-Auth Port | Response caching and background job queue |

---

## ⚙️ Core Configuration Reference

| Environment Variable | Default Value | Description |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `groq` | Active LLM inference provider (`groq`, `gemini`, `ollama`) |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Configured Groq model (supports `llama-3.3-70b-versatile`) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformer embedding model name (384 dims) |
| `TOP_K_VECTORS` | `5` | Number of dense vector passages retrieved per query |
| `TOP_K_GRAPH` | `5` | Number of multi-hop graph subgraphs retrieved per query |
| `RRF_K` | `60` | Smoothing constant in Reciprocal Rank Fusion formula |
| `TEMPERATURE` | `0.2` | Deterministic sampling temperature for grounded generation |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API gateway URL used by the React frontend |

---

## 📜 Administrative & Utility Scripts

All maintenance utilities are located in `backend/scripts/`:

```bash
# 1. Inspect database records, vector count, and graph triples:
python scripts/check_stats.py

# 2. Batch re-index and re-chunk all stored PDF papers:
python scripts/reprocess_all_papers.py

# 3. Clean and reset the Neo4j knowledge graph safely:
python scripts/clear_neo4j.py
```

---

## 🧪 Testing & Verification

The codebase includes comprehensive test suites across both backend and frontend layers:

### Backend Unit & Integration Tests (pytest)
```bash
cd backend
pytest -v
```
> **Status**: `32 passed` — Covers PDF parsing, semantic chunking, embedding generation, Cypher query construction, RRF ranking, Pydantic schemas, and API routes.

### Frontend Unit & Component Tests (Vitest)
```bash
cd frontend
npm test
```
> **Status**: `7 passed` — Covers React rendering, Zustand stores, SSE client streaming parser, and graph canvas bindings.

### Production Build Verification
```bash
cd frontend
npm run build
```
> **Status**: Successfully compiles without TypeScript warnings or bundling errors.

---

## 🔒 Security, Grounding & Reliability

- **Strict Source Grounding**: Every generated statement is constrained to evidence chunks with verified citations `[Paper, Page X]`.
- **Anti-Hallucination Guardrails**: Prompts enforce negative constraints ("If evidence does not contain the answer, state that it cannot be determined").
- **Parameter Validation**: Input queries and pagination constraints are strictly validated via Pydantic v2.
- **Failover & Multi-Provider Resilience**: Gracefully switches to secondary LLM endpoints (Gemini / Ollama) if the primary provider encounters rate limits.
- **Async Non-Blocking Architecture**: Long-running PDF ingestion tasks run in background worker threads without blocking user chat queries.

---

## 📦 Core Capabilities Summary

- 📄 **High-Fidelity PDF Parsing**: Extracts text, metadata, sections, and references with layout awareness.
- 🧬 **Automated Knowledge Graph Extraction**: Discovers research entities and typed relational triples.
- 🔀 **Reciprocal Rank Fusion (RRF)**: Dynamically balances vector similarity with graph connectivity.
- 🔮 **GNN Link Prediction**: Uncovers latent research connections and cross-domain citation possibilities.
- ⚡ **Ultra-Fast Streaming**: Sub-second token delivery powered by Groq Cloud LPU acceleration.
- 🖥️ **Editorial Research UI**: Full-fledged React 18 interface with interactive graph canvas and KaTeX math.
- 🚀 **Turnkey Deployment**: One-command Windows scripts and Docker Compose orchestration.

---

<div align="center">
  <p>Built with 🧠 for Grounded Academic & Scientific Research Intelligence</p>
  <p>Developed by <strong>Priyan-19</strong></p>
  <p>© 2026 Academic Hybrid RAG Research Platform. All Rights Reserved.</p>
</div>
