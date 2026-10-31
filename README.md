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
- 📊 **Interactive React Web UI**: A production-grade editorial research interface for paper ingestion, grounded RAG dialogues, interactive Neo4j knowledge graph exploration, GNN link prediction, and quantitative evaluation.
- ⚡ **FastAPI REST Backend**: Asynchronous microservice API providing Swagger UI documentation (`/docs`) and background worker processing.
- 📈 **Graph Neural Network (GNN) Link Prediction**: Predicts potential future research collaboration and concept connections.

---

## 🛠️ Architecture & Tech Stack

```text
               +----------------------------------+
               |     React Web UI (Port 5173)     |
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

- **Programming Language**: Python >= 3.11 & TypeScript
- **Package Manager**: `uv` (Fast Python package manager) & `npm`
- **Backend Framework**: FastAPI + Uvicorn + Pydantic v2
- **Vector Database**: PostgreSQL with `pgvector` (via SQLAlchemy Async)
- **Graph Database**: Neo4j (via Neo4j Python Driver & Cypher)
- **Caching & Job Queue**: Redis
- **Frontend Interface**: React 18 + Vite + TypeScript (Tailwind CSS, Radix, react-force-graph-2d)
- **LLM & Embeddings**: Groq Cloud (`openai/gpt-oss-120b`, Llama 3.3) / Google Gemini, Sentence Transformers (`all-MiniLM-L6-v2`)

---

## 🎨 React Frontend (New Modern Web UI)

The project includes a production-quality chatbot web UI in React that replaces the legacy Streamlit interface, styled with a warm tactile editorial design system (Newsreader typography, warm parchment `#fef9f0` canvas, sharp 90° corners, and exhibition catalog styling).

### Tech Stack
- **Framework**: React 18 + Vite + TypeScript
- **Styling**: Tailwind CSS + Custom Design System tokens
- **State Management**: Zustand (UI and conversation state) + TanStack Query (server state & caching)
- **Routing**: `react-router-dom`
- **Math & Code**: `react-markdown` + `remark-math` + `rehype-katex` + `rehype-highlight`
- **Knowledge Graph Visualizer**: `react-force-graph-2d`
- **Icons**: `lucide-react`

### Getting Started with React Frontend

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Copy the environment template
cp .env.example .env

# 3. Install dependencies
npm install

# 4. Start Vite development server
npm run dev
```

Visit **http://localhost:5173** to access the research assistant interface.

### Building for Production & Docker

```bash
# Build production bundle
npm run build

# Run via Docker
docker-compose up --build frontend
```

---

## 📁 Repository Structure

```text
.
├── PRD_LLM_Knowledge_Graph_Research_Assistant.md  # Detailed Product Requirements Document
├── modules.md                                      # Architectural Modules Blueprint
├── README.md                                       # Project Overview & Setup Guide
├── .gitignore                                      # Root Git ignore rules
├── run_all.ps1 / run_all.bat                       # One-command full-stack launchers (Root)
├── stop_all.ps1 / stop_all.bat                     # One-command full-stack shutdown scripts (Root)
├── frontend/                                       # Production React 18 + Vite Web Application
│   ├── src/
│   │   ├── api/                                    # Typed REST API layer & SSE streaming client
│   │   ├── components/                             # UI components (Chat, Graph, Papers, Sources)
│   │   ├── pages/                                  # ChatPage, PapersPage, KnowledgeGraphPage, etc.
│   │   ├── store/                                  # Zustand state management (Chat, UI, Settings)
│   │   └── types/                                  # TypeScript interface definitions
│   ├── package.json                                # NPM frontend dependencies & scripts
│   ├── tailwind.config.js                          # Editorial design system token configuration
│   └── vite.config.ts                              # Vite build & proxy configuration
└── backend/                                        # FastAPI REST Application Service
    ├── app/                                        # Core application package
    │   ├── api/v1/                                 # REST API endpoints (health, papers, chat, graph)
    │   ├── core/                                   # Application configuration & logging
    │   ├── database/                               # Postgres, Neo4j, and Redis async clients
    │   ├── graph/                                  # Graph extractors, canonicalizer & GNN
    │   ├── ingestion/                              # PDF loader, chunker & metadata extractor
    │   ├── llm/                                    # Multi-provider LLM abstraction (Groq, Gemini)
    │   ├── rag/                                    # Hybrid retriever & grounded chat service
    │   ├── schemas/                                # Pydantic v2 data models
    │   ├── services/                               # Business logic & paper management
    │   └── workers/                                # Background paper processing workers
    ├── data/                                       # Storage for PDF uploads & processed files
    │   ├── uploads/
    │   └── processed/
    ├── scripts/                                    # Utility scripts (reprocessing, stats, clear DB)
    ├── tests/                                      # Pytest suite
    ├── Dockerfile.backend                          # Backend container definition
    ├── docker-compose.yml                          # Multi-container database setup
    └── pyproject.toml / requirements.txt           # Python dependency specifications
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

#### Option A: One-Command Launcher (Recommended for Windows)

Run the automated launcher script to start Docker databases, the FastAPI backend, and the React frontend simultaneously:

**In PowerShell:**
```powershell
.\run_all.ps1
```

**Or in Command Prompt (CMD):**
```cmd
run_all.bat
```

To stop all services when done:
```powershell
.\stop_all.ps1
```
*(Or in CMD: `stop_all.bat`)*

#### Option B: Individual Terminal Commands

1. **Start Databases (Docker)**:
   ```bash
   cd backend && docker-compose up -d postgres neo4j redis
   ```

2. **Start FastAPI Backend (Port 8000)**:
   ```bash
   cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

3. **Start React Frontend (Port 5173)**:
   ```bash
   cd frontend && npm run dev
   ```

---

## 🔗 Access Points & Documentation

| Service / Interface | URL | Description |
| :--- | :--- | :--- |
| **React Web UI** | `http://localhost:5173` | Main interactive research assistant dashboard |
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
