# LLM + Knowledge Graph Research Assistant — Execution Roadmap (modules.md)

**Version:** 2.0 (Backend-First Execution Plan)  
**Status:** Approved Blueprint  
**Primary Strategy:** Complete and test the entire Backend & AI Pipeline (Phase 1) before building the Frontend Interface (Phase 2). Integrates advanced technical recommendations (Entity Canonicalization, Reciprocal Rank Fusion, Layout-Aware Parsing, and RAGAS Framework).

---

# Phase 1: Backend & AI Engine Development (Complete First)

---

## Module 0 — Infrastructure & Backend Foundation

### Objective
Establish the backend project architecture, database schemas, ORM configuration, and service connectivity for PostgreSQL (`pgvector`), Neo4j, and Redis.

### Tasks
- Setup Python project environment (FastAPI, Pydantic v2, SQLAlchemy / SQLModel).
- Configure environment variables and configuration management (`core/config.py`).
- Implement logging framework and structured exception handling (`core/logging.py`, `core/exceptions.py`).
- Initialize PostgreSQL connection pool with `pgvector` extension enabled.
- Initialize Neo4j Graph Database connection driver (`knowledge_graph/neo4j_client.py`).
- Initialize Redis connection for caching and background job queuing.
- Implement FastAPI health check endpoint (`GET /api/v1/health`) verifying DB connections.

### Deliverables
- Fully functioning FastAPI application shell with PostgreSQL, Neo4j, and Redis connections verified.

---

## Module 1 — Layout-Aware PDF Ingestion & Document Processing

### Objective
Parse research PDFs with layout awareness, extract clean structured text, preserve page/section metadata, and create chunk boundaries.

### Tasks
- Implement file upload API with size/type validation (`api/v1/papers.py`).
- Integrate layout-aware PDF parser (`PyMuPDF` / `fitz` or `GROBID` / `Marker`) to handle 2-column academic papers, figures, formulas, and reference sections cleanly.
- Implement section detection logic (Abstract, Introduction, Methodology, Results, Conclusion, References).
- Implement metadata extraction pipeline (Title, Authors, Abstract, Year, DOI).
- Build semantic chunker preserving chunk-level metadata:
  ```json
  {
    "chunk_id": "paper_001_c012",
    "paper_id": "paper_001",
    "page_number": 4,
    "section": "Methodology",
    "text": "..."
  }
  ```
- Store raw papers and structured chunks in PostgreSQL.

### Deliverables
- PDF Upload & Parsing API producing clean, metadata-tagged text chunks stored in the database.

---

## Module 2 — Embeddings & Vector Storage Engine

### Objective
Convert document text chunks into dense vector embeddings and index them in PostgreSQL using `pgvector`.

### Tasks
- Integrate embedding model (SentenceTransformers `all-MiniLM-L6-v2` / `bge-large-en` or Google Gemini Embedding API).
- Implement batch embedding generation service (`embeddings/embedding_service.py`).
- Store vector embeddings in PostgreSQL `pgvector` column.
- Configure `HNSW` (Hierarchical Navigable Small World) or `IVFFlat` index on vector column for sub-second similarity search.
- Implement vector search utility function with Top-K and cosine similarity thresholding.

### Deliverables
- Automated embedding pipeline populating indexed `pgvector` storage for instant semantic search.

---

## Module 3 — Basic Vector RAG Service

### Objective
Build a functional baseline Retrieval-Augmented Generation (RAG) pipeline for PDF question answering.

### Tasks
- Build Query Embedding service (`rag/vector_retriever.py`).
- Implement Top-K similarity vector search against chunk embeddings.
- Construct Context Builder assembling retrieved chunks into LLM prompt templates (`rag/context_builder.py`).
- Integrate initial LLM service to answer questions based strictly on retrieved context.
- Expose REST endpoint (`POST /api/v1/search/vector`).

### Deliverables
- Working baseline vector RAG API answering questions grounded in PDF chunks.

---

## Module 4 — Multi-Provider LLM Abstraction Layer

### Objective
Decouple application logic from specific LLM vendors, supporting seamless switching between Gemini API, Ollama/Llama, and local models.

### Tasks
- Define abstract base class `LLMProvider` (`llm/base.py`).
- Implement `GeminiProvider` using Google Gemini API (`llm/gemini.py`).
- Implement `LlamaProvider` using Ollama / local inference (`llm/llama.py`).
- Implement strict Pydantic structured output validation for LLM responses (`llm/structured_output.py`).
- Add fallback mechanism and retry handlers for LLM API rate limits.

### Deliverables
- Provider-agnostic LLM service layer configurable via environment variables (`LLM_PROVIDER=gemini`).

---

## Module 5 — Knowledge Graph Extraction & Entity Canonicalization

### Objective
Extract research entities and relationships from paper chunks and populate Neo4j with a canonicalized, deduplicated graph.

### Tasks
- Define Knowledge Graph Schema in Neo4j (`knowledge_graph/graph_schema.py`):
  - **Node Labels:** `Paper`, `Author`, `Concept`, `Topic`, `Model`, `Method`, `Dataset`, `Organization`.
  - **Relationship Types:** `WROTE`, `CITES`, `MENTIONS`, `USES_MODEL`, `USES_DATASET`, `TYPE_OF`, `IMPROVES`, `EVALUATED_ON`.
- Implement LLM-based Entity & Relationship Extractor using Pydantic schemas (`knowledge_graph/entity_extractor.py`, `relationship_extractor.py`).
- **Entity Resolution & Canonicalization Engine** (`knowledge_graph/entity_normalizer.py`):
  - Implement vector similarity + fuzzy string matching on extracted entity names.
  - Merge redundant nodes (e.g., canonicalize `"BERT"`, `"BERT model"`, `"Bidirectional Encoder Representations from Transformers"` to single canonical entity `"BERT"`).
- Implement Cypher Graph Builder batch-inserting canonical nodes and relationships into Neo4j (`knowledge_graph/graph_builder.py`).

### Deliverables
- Automated Knowledge Graph extraction pipeline creating deduplicated, canonical Neo4j graph networks from papers.

---

## Module 6 — Graph Retrieval Service

### Objective
Extract query entities and traverse Neo4j graph relationships to retrieve relational context.

### Tasks
- Implement Query Entity Extraction (identifying named entities, models, methods, or datasets in user questions).
- Build Cypher Query Generator for 1-hop and 2-hop graph traversals (`knowledge_graph/graph_queries.py`).
- Implement Graph Retriever retrieving connected papers, concepts, and relationship triples (`rag/graph_retriever.py`).
- Expose REST endpoint (`POST /api/v1/search/graph`).

### Deliverables
- Graph retrieval service capable of answering multi-hop relational questions (e.g., *"Which papers use BERT on the GLUE dataset?"*).

---

## Module 7 — Hybrid Retrieval & Reciprocal Rank Fusion (RRF) Engine

### Objective
Combine Vector Retrieval and Graph Retrieval into a single unified context using Reciprocal Rank Fusion (RRF) and Cross-Encoder reranking.

### Tasks
- Build `HybridRetriever` orchestrating concurrent Vector and Graph searches (`rag/hybrid_retriever.py`).
- Implement **Reciprocal Rank Fusion (RRF)** metric:
  $$\text{RRF\_Score}(d) = \frac{w_v}{k + \text{rank}_{\text{vector}}(d)} + \frac{w_g}{k + \text{rank}_{\text{graph}}(d)}$$
- Implement optional Cross-Encoder Reranker (`rag/reranker.py`) to score and select top-N hybrid context passages.
- Construct Hybrid Context Builder formatting vector text chunks + graph relational triples for LLM prompt ingestion.
- Expose REST endpoint (`POST /api/v1/search/hybrid`).

### Deliverables
- High-precision Hybrid Retrieval pipeline serving as the core intelligence engine.

---

## Module 8 — Grounded Answer Generation & Citation Guardrails

### Objective
Generate evidence-grounded answers with explicit page-level citations and strict hallucination guardrails.

### Tasks
- Implement System Prompt Template enforcing strict grounding in provided context (`llm/prompts.py`).
- Build citation citation tag extractor linking answer claims to exact `[Paper ID, Page X, Section Y]` source metadata.
- Implement "Insufficient Evidence" guardrail returning explicit fallback messages when context relevance score is low.
- Expose REST Chat endpoint (`POST /api/v1/chat`).

### Deliverables
- Production-grade research Q&A API delivering evidence-backed answers with verifiable page references.

---

## Module 9 — Citation Recommendation Engine

### Objective
Recommend relevant papers to cite for a given research statement or paragraph.

### Tasks
- Build statement analyzer converting target text into embedding vectors and entity sets.
- Execute hybrid search finding candidate papers matching both semantic concept and graph citation networks (`analysis/citation_recommender.py`).
- Calculate Citation Relevance Score based on semantic distance + co-citation graph frequency.
- Generate natural language justification for recommended citations.
- Expose REST endpoint (`POST /api/v1/citations/recommend`).

### Deliverables
- Citation recommendation API providing ranked paper suggestions with contextual reasoning.

---

## Module 10 — Research Similarity & Duplicate Detection Engine

### Objective
Analyze overlap between research papers across semantic embeddings, shared concepts, methods, and datasets.

### Tasks
- Implement multi-factor paper comparison algorithm (`analysis/similarity_detector.py`):
  $$\text{Similarity Score} = w_1 \cdot \text{Vector\_Sim} + w_2 \cdot \text{Concept\_Overlap} + w_3 \cdot \text{Method\_Overlap} + w_4 \cdot \text{Dataset\_Overlap}$$
- Generate structured breakdown highlighting exact shared concepts, models, and datasets.
- Label results objectively as *"Highly Similar Research"* (avoiding unfounded plagiarism claims).
- Expose REST endpoint (`POST /api/v1/similarity/check`).

### Deliverables
- Research similarity API returning quantitative overlap metrics and relationship breakdowns.

---

## Module 11 — Research Trend Analysis Engine

### Objective
Aggregate historical graph data to track concept frequency, temporal growth, and emerging research domains.

### Tasks
- Implement concept frequency aggregator grouped by publication year (`analysis/trend_analyzer.py`).
- Build emerging concept detector identifying rapid year-over-year frequency spikes in Neo4j.
- Generate concept co-occurrence matrix for research topic clustering.
- Expose REST endpoints (`GET /api/v1/trends`, `GET /api/v1/trends/concepts`, `GET /api/v1/trends/timeline`).

### Deliverables
- Analytics backend API serving research trend metrics and temporal concept graphs.

---

## Module 12 — Quantitative Evaluation & Benchmark Framework

### Objective
Empirically evaluate and compare system performance using RAGAS / TruLens metrics across baseline configurations.

### Tasks
- Create standardized evaluation dataset (`data/evaluation/questions.json`, `expected_answers.json`).
- Integrate **RAGAS / TruLens** automated evaluation framework measuring:
  - **Faithfulness** (Hallucination rate)
  - **Context Precision & Recall**
  - **Answer Relevance**
- Implement **Ablation Study Experiment Runner** (`scripts/evaluate_rag.py`) comparing:
  - **Experiment A**: LLM Only (Direct generation)
  - **Experiment B**: Vector RAG Only
  - **Experiment C**: Graph RAG Only
  - **Experiment D**: Hybrid RAG (Proposed System)
- Generate comparative statistical report (CSV / JSON) logging Precision@K, MRR, NDCG, and F1 scores.

### Deliverables
- Comprehensive, reproducible evaluation suite proving technical superiority of Hybrid RAG.

---

## Module 13 — Advanced GNN Research Module [COMPLETED]

### Objective
Experiment with Graph Neural Networks using PyTorch on the Knowledge Graph for link prediction and graph embeddings.

### Tasks
- [x] Implement PyTorch Graph Convolutional Network (GCN) encoder (`app/graph/gnn_link_predictor.py`).
- [x] Construct normalized graph adjacency matrix $\tilde{A}$ and entity feature vectors.
- [x] Compute node embeddings and rank prospective research links.
- [x] Expose REST endpoint `POST /api/v1/graph/predict-links` in `app/api/v1/graph.py`.
- [x] Create standalone experimentation script (`scripts/gnn_link_prediction.py`).
- [x] Add automated unit and integration tests (`tests/test_gnn_link_prediction.py`).

### Deliverables
- GNN Link Prediction Engine and API endpoint active.

---

## Module 14 — Async Workers, Security & Productionization [COMPLETED]

### Objective
Wrap all backend services in asynchronous background queues (Celery/Redis), implement authentication, rate limiting, and Docker containerization.

### Tasks
- [x] Implement async task worker (`workers/paper_processing.py`) for PDF extraction, embedding generation, and Neo4j extraction without blocking HTTP requests.
- [x] Add job status tracking database model and paper processing pipeline wrapper (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
- [x] Implement JWT authentication & password security (`api/v1/auth.py`, `core/security.py`, `models/user.py`).
- [x] Implement OAuth2 password & bearer token profile API endpoints (`POST /register`, `POST /login`, `GET /me`).
- [x] Create `Dockerfile.backend` and update `docker-compose.yml` orchestrating FastAPI, PostgreSQL (pgvector), Neo4j, Redis, and worker services.
- [x] Comprehensive test coverage with 30 passing automated unit & integration tests (`tests/test_auth_and_workers.py`).

### Deliverables
- Fully productionized, async-capable, containerized Backend API ready for Frontend integration. Phase 1 Backend Development 100% Completed!

---

# Phase 2: Frontend Application & Data Visualization (After Backend Completion)

---

## Module 15 — Frontend Foundation & UI Component System

### Objective
Initialize React + TypeScript + Vite project with TailwindCSS design system, API service layer, and state management.

### Tasks
- Scaffold React + TypeScript project with Vite (`frontend/`).
- Install TailwindCSS and configure design system (colors, typography, dark mode, glassmorphic card styles).
- Set up Axios / Fetch API client with interceptors for API authentication (`services/api.ts`).
- Setup state management (Zustand or React Query) for global app state (`stores/paperStore.ts`, `chatStore.ts`).
- Create core layout shell (Sidebar, Header, Main content container).

---

## Module 16 — Paper Management & Upload Interface

### Objective
Build frontend UI for PDF paper uploads, processing status monitoring, and document library management.

### Tasks
- Create drag-and-drop PDF upload component (`components/papers/PaperUpload.tsx`).
- Build processing job progress indicator polling `/api/v1/papers/{id}/status`.
- Build Paper Library table/grid view with filtering, search, and metadata tags (`pages/Papers.tsx`).
- Build Paper Details drawer showing parsed sections, summary, extracted entities, and metadata (`pages/PaperDetails.tsx`).

---

## Module 17 — Interactive Grounded Research Chat Interface

### Objective
Build the main chat interface supporting streaming responses, grounded citation badges, and source evidence popups.

### Tasks
- Build conversational chat UI (`pages/ResearchChat.tsx`).
- Integrate streaming response reader for real-time LLM answer delivery.
- Render interactive inline citation badges `[Paper, Page X]` opening a source preview modal.
- Add hybrid search toggle options (Vector, Graph, Hybrid mode selector).

---

## Module 18 — Interactive Knowledge Graph Visualizer

### Objective
Render an interactive 2D/3D Knowledge Graph allowing users to explore papers, concepts, methods, and datasets visually.

### Tasks
- Integrate graph visualization library (`React-Force-Graph`, `Cytoscape.js`, or `Vis.js`).
- Render nodes (color-coded by type: Paper, Concept, Model, Dataset, Author) and directed edges (`pages/KnowledgeGraph.tsx`).
- Add interactive controls: Zoom, Pan, Node Click Inspection, Node Type Filter checkboxes.
- Implement side panel displaying detailed node attributes and connected papers upon node click.

---

## Module 19 — Citation Recommendation & Similarity Studio

### Objective
Create UI screens for sentence-level citation search and side-by-side paper similarity comparison.

### Tasks
- Build Citation Finder screen (`pages/Citations.tsx`) with input text box and ranked citation results cards.
- Build Paper Similarity Comparison tool (`pages/Similarity.tsx`) with side-by-side paper selectors and overlap percentage gauges (Concept, Method, Dataset breakdown).

---

## Module 20 — Research Trends & Analytics Dashboard

### Objective
Visualize research intelligence metrics, concept timelines, and emerging topic charts.

### Tasks
- Integrate charting library (`Recharts` or `Chart.js`).
- Build Dashboard overview screen (`pages/Dashboard.tsx`) displaying total paper counts, concept counts, and recent activity.
- Build Trends dashboard (`pages/Trends.tsx`) displaying year-by-year concept growth area charts, emerging concept clouds, and topic co-occurrence charts.

---

## Module 21 — Evaluation Results & Benchmark Visualizer

### Objective
Display quantitative benchmark metrics and ablation study results directly in the UI.

### Tasks
- Build Evaluation results view (`pages/Evaluation.tsx`) rendering precision/recall tables and bar charts comparing *LLM-Only*, *Vector RAG*, *Graph RAG*, and *Hybrid RAG*.
- Add test query playground allowing interactive verification of evidence grounding scores.

---

# Execution Order Checklist

```text
[ ] Phase 1: Backend Development
    [x] Module 0: Infrastructure & Backend Foundation
    [x] Module 1: Layout-Aware PDF Ingestion
    [x] Module 2: Embeddings & Vector Storage (pgvector)
    [x] Module 3: Basic Vector RAG Service
    [x] Module 4: Multi-Provider LLM Abstraction Layer
    [x] Module 5: Knowledge Graph Extraction & Canonicalization (Neo4j)
    [x] Module 6: Graph Retrieval Service
    [x] Module 7: Hybrid Retrieval & Reciprocal Rank Fusion (RRF)
    [x] Module 8: Grounded Answer Generation & Citations
    [x] Module 9: Citation Recommendation Engine
    [x] Module 10: Research Similarity Engine
    [x] Module 11: Research Trend Analysis Engine
    [x] Module 12: Quantitative Evaluation & RAGAS Framework
    [ ] Module 13: Advanced GNN Research Module (Optional)
    [ ] Module 14: Async Background Workers & Backend Dockerization

[ ] Phase 2: Frontend Development (Starts after Phase 1 completion)
    [ ] Module 15: Frontend Foundation & Design System
    [ ] Module 16: Paper Management UI
    [ ] Module 17: Grounded Research Chat Interface
    [ ] Module 18: Interactive Knowledge Graph Visualizer
    [ ] Module 19: Citation & Similarity Studio
    [ ] Module 20: Trends & Analytics Dashboard
    [ ] Module 21: Evaluation Benchmark UI
```
