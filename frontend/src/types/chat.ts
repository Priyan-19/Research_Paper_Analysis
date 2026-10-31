import { CitationBadge, SearchMode } from "./api";

export interface RetrievedSource {
  source_index: number;
  source_type: "vector" | "graph" | "hybrid";
  paper_id: string;
  paper_title: string;
  page_number?: number | null;
  section_name?: string | null;
  chunk_id?: string;
  score?: number;
  snippet: string;
  relationship?: string;
  source_entity?: string;
  target_entity?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  search_mode?: SearchMode;
  citations?: CitationBadge[];
  retrieved_sources?: RetrievedSource[];
  isStreaming?: boolean;
  metadata?: {
    llm_provider?: string;
    execution_time_seconds?: number;
    total_citations?: number;
    insufficient_evidence?: boolean;
    paper_id?: string | null;
    chunks_count?: number;
    graph_hops?: number;
  };
}

export interface Conversation {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  isPinned?: boolean;
  messages: ChatMessage[];
  paperScope?: string | null; // null = all papers
}

