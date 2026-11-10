# Research Assistant — React Web UI

Modern, production-grade web application for the **LLM + Knowledge Graph Research Assistant**.

Built with React 18, Vite, TypeScript, and Tailwind CSS, following a warm tactile editorial design system (Newsreader typography, warm parchment `#fef9f0` canvas, 0px border-radius, and exhibition catalog styling).

For full system overview and backend documentation, please see the [Root README](file:///d:/FY/README.md).

---

## 🚀 Key Modules & Pages

1. **Grounded Research Chat (`/chat`)**:
   - Conversational RAG interface with real-time typewriter token streaming and AbortController cancellation.
   - Interactive citation chips (`[1]`, `[Paper: ...]`, `[Graph: ...]`) linking to retrieved context passages.
   - Grounded evidence drawer showing document snippets, section titles, and page numbers.
   - Retrieval mode switching: **Hybrid RAG** (Reciprocal Rank Fusion), **Vector Semantic**, and **Graph Traversal**.
   - Paper scope filtering (query across all papers or restrict to a single PDF).

2. **Research Papers Index (`/papers`)**:
   - Drag-and-drop PDF paper uploader with real-time processing status.
   - Ingested paper repository table showing metadata (authors, year, page count, file size, processing status).
   - Paper details modal displaying extracted abstracts, sections, and chunk breakdown.

3. **Knowledge Graph Explorer (`/graph`)**:
   - Interactive 2D force-directed knowledge graph canvas powered by `react-force-graph-2d`.
   - Color-coded entity nodes (`CONCEPT`, `METHOD`, `DATASET`, `MODEL`, `AUTHOR`, `TASK`, `METRIC`).
   - Node click inspection drawer showing relationships, connected neighbors, and quick-prompt generation.
   - Automated Entity Canonicalization breakdown showing live Neo4j node and relationship distributions.
   - Graph Neural Network (GNN) Link Prediction interface for novel research hypothesis discovery.

4. **Trends & Quantitative Analytics (`/analytics`)**:
   - Corpus overview metrics (total papers, dense vector chunks, Neo4j entities, relational triples).
   - Extracted concept frequency leaderboards.
   - Quantitative ablation benchmark report (comparing Faithfulness, Answer Relevance, Context Precision, Recall, and MRR).
   - Sentence-level Citation Recommender.
   - Cross-Paper Similarity Detector.

5. **System Settings (`/settings`)**:
   - Live FastAPI backend connectivity indicator.
   - Configured LLM Reasoning Engine display (Groq Cloud `openai/gpt-oss-120b`).
   - Calibration sliders for Top-K evidence retrieval and sampling temperature.
   - Light / Dark parchment theme toggle.

---

## 🛠️ Tech Stack & Dependencies

- **Framework**: React 18 + Vite 5 + TypeScript (strict mode)
- **Styling**: Tailwind CSS 3.4 with custom editorial design tokens
- **Icons**: Lucide React
- **State Management**:
  - `zustand` with local storage persistence (`useChatStore`, `useUIStore`, `useSettingsStore`)
  - `@tanstack/react-query` for server state caching, request deduplication, and polling
- **Data Rendering**:
  - `react-markdown` + `remark-gfm`
  - `remark-math` + `rehype-katex` (KaTeX for academic LaTeX equations)
  - `rehype-highlight` (syntax-highlighted code blocks)
- **Graph Visualization**: `react-force-graph-2d` + HTML5 Canvas
- **Testing & Quality**: Vitest 5+, `@testing-library/react`, `@testing-library/jest-dom`, `@vitest/coverage-v8`, Oxlint

---

## 🧪 Testing, Quality Assurance & Coverage

The frontend features a comprehensive test suite covering Zustand state stores, API clients, UI primitives, and page components.

### Test Metrics

- **Total Test Cases**: **28 tests across 10 test files**
- **Test Pass Rate**: **100% (28/28 passed)**
- **Overall Line Coverage**: **65.85%** (Exceeds 60% minimum threshold)
- **Production Build Status**: Clean compile (`tsc -b && vite build` in ~3.8s)

### Running Tests Locally

```bash
# 1. Run full Vitest suite in terminal:
npm test

# 2. Run test suite with V8 coverage report and threshold checks:
npm run test:cov

# 3. Run linting checks:
npm run lint

# 4. Run TypeScript type check & production build:
npm run build
```

### Test Architecture

- **`src/store/*.test.ts`**: Verifies Zustand state mutations, local storage persistence, streaming message appends, reset behaviors, and configuration updates (`useChatStore.test.ts`, `useSettingsStore.test.ts`, `useUIStore.test.ts`).
- **`src/api/client.test.ts`**: Verifies Axios base client, timeout configurations, default headers, and interceptor behaviors.
- **`src/components/ui/*.test.tsx`**: Tests component rendering, variant styling, and accessibility for UI primitives (`Button.test.tsx`, `Card.test.tsx`, `Badge.test.tsx`).
- **`src/components/chat/*.test.tsx`**: Tests citation badges and empty state presentation (`CitationChip.test.tsx`, `EmptyState.test.tsx`).
- **`src/pages/SettingsPage.test.tsx`**: Verifies settings form inputs, API base URL modifications, and store updates.

---

## 🔄 Automated CI/CD Workflows

Frontend changes are verified automatically via GitHub Actions:

- **`frontend-ci.yml`**: Triggers on push/PR for `frontend/**`. Sets up Node.js 20, runs `npm ci`, runs Oxlint, validates TypeScript compilation (`tsc -b`), builds production bundle (`vite build`), runs `vitest` with coverage, and uploads coverage artifacts.
- **`docker-build.yml`**: Compiles and verifies the frontend Docker image (`frontend/Dockerfile`) using NGINX and multi-stage Buildx caching.
- **`security-checks.yml`**: Executes `npm audit --audit-level=critical` to detect package CVEs.

---

## 🏃 Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Ensure `VITE_API_BASE_URL` points to your backend (`http://localhost:8000`).

### 3. Run Development Server (Port 5173)
```bash
npm run dev
```

### 4. Build Production Distribution
```bash
npm run build
```

---

## 📂 Project Structure

```text
frontend/
├── src/
│   ├── api/             # Typed API clients (health, papers, chat, graph, analytics, streaming)
│   │   ├── client.ts    # Axios instance & error handling
│   │   └── client.test.ts
│   ├── components/
│   │   ├── chat/        # Message bubbles, composer, citation chips, empty state
│   │   ├── graph/       # Node details drawer, canonicalization tab, link prediction tab
│   │   ├── layout/      # AppLayout, collapsible Sidebar, Header, Toasts
│   │   ├── papers/      # Paper uploader, details modal
│   │   ├── sources/     # Grounded evidence side drawer (Papers & Graph tabs)
│   │   └── ui/          # Buttons, Cards, Badges, Modals
│   ├── pages/           # ChatPage, PapersPage, KnowledgeGraphPage, AnalyticsPage, SettingsPage
│   │   └── SettingsPage.test.tsx
│   ├── store/           # Zustand stores (useChatStore, useUIStore, useSettingsStore)
│   │   ├── useChatStore.test.ts
│   │   ├── useSettingsStore.test.ts
│   │   └── useUIStore.test.ts
│   ├── types/           # TypeScript API schemas & chat data models
│   ├── App.tsx          # Root router & layout composition
│   ├── index.css        # Tailwind directives & CSS custom variables
│   └── main.tsx         # React DOM root entry
├── index.html           # HTML5 entry with Newsreader font & KaTeX CDN
├── package.json         # Dependencies, Vitest scripts & coverage runner
├── tailwind.config.js   # Editorial design palette configuration
├── vite.config.ts       # Vite config, dev proxy, and Vitest V8 coverage setup
├── Dockerfile           # Production NGINX web server container
└── nginx.conf           # SPA routing & reverse proxy configuration
```
