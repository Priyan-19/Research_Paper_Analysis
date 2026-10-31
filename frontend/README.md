# Research Assistant — React Web UI

Modern, production-grade web application for the **LLM + Knowledge Graph Research Assistant**.

Built with React 18, Vite, TypeScript, and Tailwind CSS, following a warm tactile editorial design system (Newsreader typography, warm parchment `#fef9f0` canvas, 0px border-radius, and exhibition catalog styling).

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

- **Framework**: React 18 + Vite 5 + TypeScript (strict)
- **Styling**: Tailwind CSS with custom editorial design tokens
- **Icons**: Lucide React
- **State Management**:
  - `zustand` with persistence (conversations, search mode, paper scope, UI layout)
  - `@tanstack/react-query` for server state, caching, and auto-polling
- **Data Rendering**:
  - `react-markdown` + `remark-gfm`
  - `remark-math` + `rehype-katex` (KaTeX for academic LaTeX equations)
  - `rehype-highlight` (syntax-highlighted code blocks with copy-to-clipboard)
- **Graph Visualization**: `react-force-graph-2d`
- **Testing**: Vitest + `@testing-library/react` + `@testing-library/jest-dom`

---

## 🏃 Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Run Development Server (Port 5173)
```bash
npm run dev
```

### 3. Run Unit Tests
```bash
npm test
```

### 4. Build Production Bundle
```bash
npm run build
```

---

## 📂 Project Structure

```text
frontend/
├── src/
│   ├── api/             # Typed API clients (health, papers, chat, graph, analytics, streaming)
│   ├── components/
│   │   ├── chat/        # Message bubbles, composer, citation chips, empty state
│   │   ├── graph/       # Node details drawer, canonicalization tab, link prediction tab
│   │   ├── layout/      # AppLayout, collapsible Sidebar, Header, Toasts
│   │   ├── papers/      # Paper uploader, details modal
│   │   ├── sources/     # Grounded evidence side drawer (Papers & Graph tabs)
│   │   └── ui/          # Buttons, Cards, Badges, Modals
│   ├── pages/           # ChatPage, PapersPage, KnowledgeGraphPage, AnalyticsPage, SettingsPage
│   ├── store/           # Zustand stores (useChatStore, useUIStore, useSettingsStore)
│   ├── types/           # TypeScript API schemas & chat data models
│   ├── App.tsx          # Root router & layout composition
│   ├── index.css        # Tailwind directives & CSS custom variables
│   └── main.tsx         # React DOM root entry
├── index.html           # HTML5 entry with Newsreader font & KaTeX CDN
├── tailwind.config.js   # Editorial design palette configuration
└── vite.config.ts       # Vite config with dev proxy to FastAPI (8000)
```
