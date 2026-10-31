// Derived directly from backend/app/schemas/

export type SearchMode = "hybrid" | "vector" | "graph";

export interface CitationBadge {
  paper_id: string;
  paper_title: string;
  page_number?: number | null;
  section_name?: string | null;
  citation_tag: string;
  snippet?: string | null;
}

export interface ChatRequest {
  query: string;
  search_mode?: SearchMode;
  paper_id?: string | null;
  top_k?: number;
  temperature?: number;
}

export interface ChatResponse {
  query: string;
  answer: string;
  search_mode: string;
  total_citations: number;
  citations: CitationBadge[];
  insufficient_evidence: boolean;
  llm_provider: string;
  execution_time_seconds: number;
}

export interface RAGSourceItem {
  source_index: number;
  paper_id: string;
  paper_title: string;
  page_number?: number | null;
  section_name?: string | null;
  chunk_id: string;
  similarity_score: number;
}

export interface VectorRAGResponse {
  query: string;
  answer: string;
  total_sources: number;
  sources: RAGSourceItem[];
  llm_provider: string;
  execution_time_seconds: number;
}

export interface ChunkResponse {
  id: string;
  paper_id: string;
  chunk_index: number;
  page_number: number;
  section_name: string;
  text: string;
  char_length: number;
  token_count: number;
  created_at: string;
}

export interface ChunkListResponse {
  paper_id: string;
  total_chunks: number;
  chunks: ChunkResponse[];
}

export interface PaperResponse {
  id: string;
  filename: string;
  title?: string | null;
  authors?: string[];
  abstract?: string | null;
  publication_year?: number | null;
  file_size_bytes: number;
  total_pages: number;
  status: "uploaded" | "processing" | "indexed" | "failed" | string;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaperDetailResponse extends PaperResponse {
  total_chunks: number;
  chunks?: ChunkResponse[];
}

export interface PaperListResponse {
  total: number;
  papers: PaperResponse[];
}

export interface GraphNodeResponse {
  id: string;
  name: string;
  type: string;
  description?: string | null;
}

export interface GraphEdgeResponse {
  source: string;
  target: string;
  relation_type: string;
  description?: string | null;
}

export interface PaperGraphResponse {
  paper_id: string;
  paper_title: string;
  total_nodes: number;
  total_edges: number;
  nodes: GraphNodeResponse[];
  edges: GraphEdgeResponse[];
}

export interface GraphStatsResponse {
  total_nodes: number;
  total_relationships: number;
  entity_type_counts: Record<string, number>;
  relationship_type_counts: Record<string, number>;
}

export interface GNNLinkPredictionItem {
  target_entity: string;
  link_probability: number;
  similarity_score: number;
  gnn_recommendation: string;
}

export interface GNNPredictLinksResponse {
  source_entity: string;
  total_candidates_evaluated: number;
  predicted_links: GNNLinkPredictionItem[];
}

export interface ServiceHealth {
  connected: boolean;
  version?: string;
  details?: Record<string, any>;
  [key: string]: any;
}

export interface SystemHealthResponse {
  status: "healthy" | "degraded" | "offline";
  app_name: string;
  version: string;
  services: {
    postgresql?: ServiceHealth;
    neo4j?: ServiceHealth;
    redis?: ServiceHealth;
    [key: string]: any;
  };
}

export interface TrendOverviewResponse {
  total_papers: number;
  total_chunks: number;
  total_graph_nodes: number;
  total_graph_edges: number;
  top_concepts: Array<{ concept: string; count: number }>;
  year_distribution: Record<string, number>;
}

export interface EvaluationReportResponse {
  benchmark_timestamp: string;
  total_queries_evaluated: number;
  metrics_by_system: Record<string, {
    faithfulness: number;
    answer_relevance: number;
    context_precision: number;
    context_recall: number;
    mrr: number;
    avg_latency_seconds: number;
  }>;
}
