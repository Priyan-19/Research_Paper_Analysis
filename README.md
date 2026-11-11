<div align="center">

# 🧠 LLM + Knowledge Graph Research Assistant (v2.0.0)
### Enterprise Tri-Hybrid RAG Intelligence Platform for Academic & Scientific Research Papers 🌐📚

[![Vite](https://img.shields.io/badge/VITE-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![React](https://img.shields.io/badge/REACT%2018-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TYPESCRIPT-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TAILWIND%20CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![FastAPI](https://img.shields.io/badge/FASTAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/PYTHON%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/POSTGRESQL%20PGVECTOR-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Neo4j](https://img.shields.io/badge/NEO4J%20GRAPH-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com/)
[![Redis](https://img.shields.io/badge/REDIS-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![PyTorch](https://img.shields.io/badge/PYTORCH%20GNN-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Groq Cloud](https://img.shields.io/badge/GROQ%20CLOUD-F55036?style=for-the-badge&logo=meta&logoColor=white)](https://groq.com/)
[![Google Gemini](https://img.shields.io/badge/GOOGLE%20GEMINI-8E75C2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)

**LLM + Knowledge Graph Research Assistant** is an enterprise-grade academic research intelligence platform engineered to ingest, index, cross-reference, reason over, and synthesize complex scientific literature. By unifying dense vector similarity search, BM25 lexical keyword retrieval, structured multi-hop graph traversal, and supervised Graph Convolutional Networks (GCN), the platform delivers verifiable, hallucination-free research intelligence with strict citation provenance.

</div>

---

## 📚 Table of Contents
- [Project Overview](#-project-overview)
- [What's New in v2.0.0](#-whats-new-in-v200)
- [System Architecture](#-system-architecture)
- [Core Feature Matrix](#-core-feature-matrix)
- [Technical Documentation Suite](#-technical-documentation-suite)
- [Technology Stack](#-technology-stack)
- [Repository Structure](#-repository-structure)
- [Quick Start Guide](#-quick-start-guide)
- [Testing & Quality Verification](#-testing--quality-verification)
- [API Reference](#-api-reference)
- [License](#-license)

---

## 📖 Project Overview

Traditional PDF chatbots and standard RAG implementations rely solely on dense vector retrieval. While semantic vector search retrieves topically related passages, it fails systematically when tasked with:
1. **Multi-Hop Relational Synthesis**: Tracing cross-paper methodologies, benchmarks, and architectural dependencies.
2. **Exact Terminology & Model Versions**: Accurately distinguishing between numbered model iterations (e.g., *GPT-3* vs *GPT-4*, *ResNet-50* vs *ResNet-101*) without fuzzy merge errors.
3. **Structured Tabular Data**: Preserving benchmark comparisons and experimental results formatted in PDF tables.
4. **Predictive Research Discovery**: Uncovering latent, unasserted connections between emerging methods and target domains.

This platform solves these foundational challenges through a **Tri-Hybrid Retrieval Engine** (Dense Vector + BM25 Lexical + Neo4j Graph Cypher), **Atomic Claim-Level Verification**, and a **Supervised PyTorch Graph Neural Network (GNN)**, orchestrated via an asynchronous FastAPI gateway and an editorial React 18 single-page application.

---

## 🌟 What's New in v2.0.0

- **Full-Paper Chunk-Level Graph Extraction**: Replaced arbitrary 2,000-character truncations with a sliding-window chunk extractor and graph merger that captures entities and relationships across entire documents with full provenance (`paper_id`, `page_number`, `section_name`, `chunk_id`).
- **Hybrid Entity Canonicalization**: Added Levenshtein string similarity matching, alias dictionary normalization, model version protection (`are_distinct_versions`), and an audit trail for borderline matches.
- **Genuine Supervised GNN Link Prediction**: Replaced pseudo-random feature hashing with 384-dimensional dense semantic vectors, a 2-layer Graph Convolutional Network (`GCNEncoder`), negative edge sampling, and checkpoint saving (`data/models/gnn_link_predictor.pt`).
- **Structured PDF & Table Extraction**: Integrated PyMuPDF `find_tables()` to format tabular data into Markdown syntax, paired with an OCR fallback (`pytesseract`) for scanned pages (<50 characters).
- **Tri-Hybrid RAG Retrieval**: Fuses Dense Vector Search, BM25 Lexical Retrieval, and Neo4j Graph Cypher Traversal via Reciprocal Rank Fusion (RRF, $K=60$) with Cross-Encoder reranking fallback.
- **Claim-Level Grounding & Verification**: Decomposes answers into atomic assertions and verifies each against retrieved context tokens, classifying claims as `SUPPORTED` or `UNSUPPORTED` with zero hallucinated fallback citations.
- **Non-Blocking Background Tasks & Multi-Tenancy**: Added non-blocking PDF uploads with real-time status polling (`GET /api/v1/papers/{id}/status`), database-level tenant scoping (`user_id`), and backward-compatible optional JWT authentication.
- **Resilience & Fault Tolerance**: Fixed trend analysis runtime bugs and implemented exponential backoff retries with jitter on external LLM rate limits.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Frontend Single-Page App (Port 5173)"]
        UI["React 18 + Vite + TypeScript"]
        ChatUI["Typewriter Streaming Chat (SSE)"]
        GraphViz["ForceGraph2D Canvas Visualizer"]
        StatusPoll["Upload Progress Poller"]
    end

    subgraph Gateway ["FastAPI Gateway & Auth (Port 8000)"]
        Router["FastAPI Application Router (/api/v1)"]
        AuthGuard["JWT Tenant Access Guard"]
        WorkerPool["FastAPI Background Tasks"]
    end

    subgraph IngestionEngine ["Structured Document Ingestion"]
        PyMuPDF["PyMuPDF (fitz) Layout Parser"]
        TableParser["Table Extractor (Markdown Grids)"]
        OCRFallback["Tesseract OCR Fallback (<50 chars)"]
        Chunker["Semantic Section Chunker"]
        Provenance["Provenance Mapper (Page / Section / Chunk)"]
    end

    subgraph GraphCore ["Knowledge Graph & GNN Engine"]
        Extractor["Full-Paper Graph Extractor"]
        Canonicalizer["Hybrid Entity Canonicalizer"]
        GCN["Supervised GNN Link Predictor (PyTorch)"]
        Neo4j[("Neo4j Graph Database (Port 7687)")]
    end

    subgraph TriHybridRAG ["Tri-Hybrid Retrieval Engine"]
        DenseSearch["Dense Vector Search (pgvector)"]
        BM25Search["BM25 Lexical Keyword Engine"]
        CypherSearch["Neo4j Cypher Traversal"]
        RRF["Reciprocal Rank Fusion (K=60)"]
        Reranker["Cross-Encoder Reranker Fallback"]
    end

    subgraph Synthesis ["Synthesis & Verification"]
        LLM["Groq Cloud / Google Gemini"]
        ClaimVerifier["Claim-Level Verification Engine"]
        CitationGuard["Strict Citation Guard"]
    end

    subgraph Persistence ["Data Infrastructure"]
        PG[("PostgreSQL 16 + pgvector (Port 5432)")]
        RedisDB[("Redis Cache (Port 6379)")]
    end

    UI --> Router
    Router --> AuthGuard
    AuthGuard --> WorkerPool

    WorkerPool --> PyMuPDF
    PyMuPDF --> TableParser
    PyMuPDF --> OCRFallback
    TableParser --> Chunker
    Chunker --> Provenance

    Provenance --> Extractor
    Extractor --> Canonicalizer
    Canonicalizer --> Neo4j
    Neo4j --> GCN

    Provenance --> DenseSearch
    Provenance --> BM25Search
    DenseSearch --> PG
    BM25Search --> PG

    Router --> TriHybridRAG
    TriHybridRAG --> DenseSearch
    TriHybridRAG --> BM25Search
    TriHybridRAG --> CypherSearch
    DenseSearch --> RRF
    BM25Search --> RRF
    CypherSearch --> RRF
    RRF --> Reranker

    Reranker --> LLM
    LLM --> ClaimVerifier
    ClaimVerifier --> CitationGuard
    CitationGuard --> ChatUI
    Router --> RedisDB
```

---

## ⚡ Core Feature Matrix

### 1. Ingestion & Structured Parsing
- **Markdown Tables**: Automatically identifies table cells and formats them into Markdown syntax (`| col | ... |`), preserving benchmark metrics and experimental comparisons.
- **Scanned Document OCR**: Seamlessly runs `pytesseract` when extracted text is $<50$ characters, gracefully falling back to native text extraction if the OS Tesseract binary is absent.
- **Provenance Retention**: Every chunk, entity, and relationship retains its source `paper_id`, `page_number`, `section_name`, and `chunk_id`.

### 2. Knowledge Graph & GNN Link Prediction
- **Chunk-Level Extraction**: Processes complete papers using sliding windows without hitting LLM context limits or dropping later sections.
- **Version Disambiguation**: Enforces version protection so that model versions (e.g., `GPT-3` vs `GPT-4`, `Llama-2` vs `Llama-3`) are never conflated.
- **Genuine GNN Training**: Trains a 2-layer Graph Convolutional Network (`GCNEncoder`) with negative edge sampling, `BCEWithLogitsLoss`, and checkpoint persistence (`gnn_link_predictor.pt`).
- **Honesty Safeguard**: Returns `trained: False` with descriptive diagnostic feedback when graph topology is sparse (<4 entities or <3 edges) rather than producing fake predictions.

### 3. Tri-Hybrid Retrieval & Reranking
- **Dense Vector Search**: `pgvector` HNSW cosine distance over 384-dimensional chunk embeddings.
- **BM25 Lexical Search**: Exact term frequency-inverse document frequency keyword matching catching specific abbreviations, acronyms, and model tags.
- **Graph Cypher Traversal**: Outward 2-hop structural traversal returning relational context with edge provenance.
- **Reciprocal Rank Fusion**: Merges scores dynamically:
  $$RRF(d) = \sum_{c \in Channels} \frac{w_c}{60 + \text{rank}_c(d)}$$
- **Cross-Encoder Reranking**: Optional second-stage reranker scoring candidate passages with automatic fallback.

### 4. Claim-Level Verification & Citations
- **Atomic Claim Decomposition**: Separates answers into independent propositional claims while removing citation markers and meta-disclaimers.
- **Evidence Support Verification**: Computes token alignment ratios against retrieved context, tagging claims as `SUPPORTED` or `UNSUPPORTED`.
- **Zero Hallucinated Citations**: Rejects fabricated fallback citations; every returned citation tag corresponds directly to a retrieved chunk.

### 5. Multi-Tenancy & Background Scalability
- **Asynchronous Upload**: `POST /api/v1/papers/upload` returns an HTTP 202 immediately with a job ID.
- **Job Status Polling**: `GET /api/v1/papers/{id}/status` provides real-time progress across 6 ingestion phases.
- **Tenant Isolation**: Papers and chunks are scoped to `user_id` in PostgreSQL while maintaining public access for legacy records (`user_id = NULL`).

---


## 🛠️ Technology Stack

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI 0.110+, Uvicorn (ASGI) | High-throughput asynchronous REST microservice (`/api/v1`) |
| **Database ORM** | SQLAlchemy 2.0 (Async), `asyncpg` | Asynchronous PostgreSQL connection pooling |
| **Vector Database** | PostgreSQL 16 + `pgvector` | 384-dimensional dense vector storage & HNSW cosine index |
| **Graph Database** | Neo4j 5 Community Edition, Cypher | Property graph storage, Cypher multi-hop graph queries |
| **In-Memory Cache & Queue** | Redis 7 | Query response caching and asynchronous task queuing |
| **Graph Neural Network** | PyTorch 2.0+ (GCN) | Supervised link prediction with negative sampling |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | Dense semantic passage & node feature representations |
| **Lexical Search** | BM25 In-Memory Algorithm | Lexical keyword retrieval for exact technical terms |
| **PDF Ingestion** | PyMuPDF (`fitz`), `pytesseract` | Layout-aware parsing, table detection, and OCR fallback |
| **LLM Inference** | Groq Cloud (`openai/gpt-oss-120b`), Google Gemini | Reasoning, structured entity extraction, and synthesis |
| **Frontend Framework** | React 18, Vite 5, TypeScript 5.5 | Reactive, typed single-page application |
| **Graph Visualization** | `react-force-graph-2d`, HTML5 Canvas | Dynamic force-directed graph exploration |
| **Testing** | `pytest`, `pytest-asyncio`, `vitest` | Unit, integration, and component testing |

---

## 📂 Repository Structure

```text
d:/FY/
├── docs/                                           # Comprehensive Documentation Suite
│   ├── ARCHITECTURE.md                             # Architectural diagrams and pipeline specs
│   ├── CHANGELOG.md                                # Systematic release changelog
│   ├── DATABASE_MIGRATIONS.md                      # PostgreSQL & Neo4j schema migrations
│   ├── ENGINEERING_AUDIT.md                        # Phase 0 codebase audit report
│   ├── IMPLEMENTATION_PLAN.md                      # Phase-by-phase implementation record
│   ├── KNOWN_LIMITATIONS.md                        # Operational boundaries and requirements
│   └── TESTING_REPORT.md                           # Verification logs and test breakdown
│
├── backend/                                        # FastAPI Application Service
│   ├── app/
│   │   ├── api/v1/                                 # API route handlers
│   │   │   ├── chat.py                             # Grounded chat & SSE streaming
│   │   │   ├── graph.py                            # Graph queries & GNN link prediction
│   │   │   ├── health.py                           # Health checks & DB status
│   │   │   ├── papers.py                           # Background upload & status polling
│   │   │   └── search.py                           # Tri-Hybrid search endpoint
│   │   ├── core/                                   # Configuration, logging & security
│   │   │   ├── config.py                           # Pydantic v2 settings
│   │   │   ├── logging.py                          # Structured logging
│   │   │   └── security.py                         # JWT auth & tenant dependencies
│   │   ├── database/                               # Database clients (Postgres, Neo4j, Redis)
│   │   ├── embeddings/                             # Embedding service & vector store with BM25
│   │   ├── evaluation/                             # Claim decomposition & faithfulness engine
│   │   ├── graph/                                  # Full-paper extractor, canonicalizer, GNN
│   │   ├── ingestion/                              # PyMuPDF loader, table extractor, chunker
│   │   ├── llm/                                    # Groq & Gemini adapters with retry backoff
│   │   ├── models/                                 # SQLAlchemy models (Paper, Chunk, ProcessingJob)
│   │   ├── rag/                                    # Tri-Hybrid retriever, citation guard, chat
│   │   ├── schemas/                                # Pydantic request & response schemas
│   │   ├── services/                               # Business logic & background task worker
│   │   └── main.py                                 # FastAPI application entrypoint
│   ├── data/
│   │   ├── evaluation/questions.json               # 50 curated benchmark questions
│   │   ├── models/                                 # GNN model checkpoints
│   │   └── uploads/                                # Staged PDF uploads
│   ├── scripts/                                    # Evaluation & maintenance scripts
│   │   └── evaluate_rag.py                         # Automated RAG evaluation benchmark
│   └── tests/                                      # Pytest unit & integration test suite
│
├── frontend/                                       # React 18 + Vite Modern Web UI
│   ├── src/
│   │   ├── api/                                    # Typed backend client & SSE consumer
│   │   ├── components/                             # Reusable UI & chat components
│   │   ├── pages/                                  # Application pages (Chat, Papers, Graph, Analytics)
│   │   └── store/                                  # Zustand state stores
│   └── package.json                                # Frontend dependencies & Vitest runner
│
├── run_all.ps1 / run_all.bat                       # One-command full-stack launchers
├── stop_all.ps1 / stop_all.bat                     # One-command full-stack shutdown scripts
├── .gitignore                                      # Comprehensive Git exclusion rules
└── README.md                                       # Master Project Documentation
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: `3.11` or `3.12`
- **Node.js**: `v18.0.0` or higher & `npm`
- **Docker Desktop**: For running PostgreSQL (`pgvector`), Neo4j, and Redis

### 1. Environment Setup

Copy example environment variables and configure your API keys:
```bash
cp backend/.env.example backend/.env
```

Configure `backend/.env`:
```env
# Server Configuration
DEBUG=true
SECRET_KEY=super_secret_jwt_key_change_me_in_production_32bytes!

# LLM Providers (Groq Cloud recommended for high speed)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Databases
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/kg_research_db
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
REDIS_URL=redis://localhost:6379/0
```

### 2. Start Database Services

Launch containerized PostgreSQL (`pgvector`), Neo4j, and Redis:
```bash
docker compose up -d
```

### 3. Launch the Application

You can use the one-click startup scripts:
```powershell
# Windows PowerShell
.\run_all.ps1

# Windows CMD
run_all.bat
```

Or start the backend and frontend independently:
```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Testing & Quality Verification

### Run Backend Unit Tests (Pytest)
```bash
cd backend
pytest tests/unit/ -v
```
**Results: 78 / 78 passed (100% success rate)**

### Run Frontend Unit Tests (Vitest)
```bash
cd frontend
npm test
```
**Results: 10 test files passed, 28 / 28 tests passed (100% success rate)**

### Build Frontend for Production
```bash
cd frontend
npm run build
```
**Results: 3,208 modules transformed cleanly in 3.05s with 0 errors.**

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/papers/upload` | Asynchronous PDF upload; returns HTTP 202 with job ID |
| `GET` | `/api/v1/papers/{id}/status` | Poll background ingestion progress and step details |
| `GET` | `/api/v1/papers/` | List papers scoped to authenticated user or public |
| `GET` | `/api/v1/papers/{id}` | Retrieve paper details and metadata |
| `DELETE` | `/api/v1/papers/{id}` | Delete paper, vector chunks, and Neo4j graph triples |
| `POST` | `/api/v1/chat/` | Synchronous grounded question-answering |
| `POST` | `/api/v1/chat/stream` | Real-time Server-Sent Events (SSE) token streaming |
| `POST` | `/api/v1/graph/predict-links` | GNN link prediction for prospective scientific connections |
| `POST` | `/api/v1/graph/extract` | Extract entities and relationships from paper chunks |
| `GET` | `/api/v1/search/` | Execute Tri-Hybrid (Dense + BM25 + Graph) search |
| `GET` | `/api/v1/health` | System health check and database connectivity status |

---

## 📄 License

This project is licensed under the MIT License — see the LICENSE file for details.

---

<div align="center">

Built with 🌿 for Academic Research Intelligence

Developed by Priyan

© 2026 Academic Research Intelligence System. All Rights Reserved.

</div>
