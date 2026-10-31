import { apiClient } from "./client";
import {
  GraphStatsResponse,
  PaperGraphResponse,
  GNNPredictLinksResponse,
} from "../types/api";

export async function fetchGraphStats(): Promise<GraphStatsResponse> {
  const res = await apiClient.get<GraphStatsResponse>("/api/v1/graph/stats");
  return res.data;
}

export async function fetchPaperGraph(paperId: string): Promise<PaperGraphResponse> {
  const res = await apiClient.get<PaperGraphResponse>(`/api/v1/graph/paper/${paperId}`);
  return res.data;
}

export async function extractPaperGraph(paperId: string): Promise<{
  paper_id: string;
  paper_title: string;
  entities_extracted: number;
  relationships_extracted: number;
  message: string;
}> {
  const res = await apiClient.post(`/api/v1/graph/extract/${paperId}`);
  return res.data;
}

export async function predictGnnLinks(
  sourceEntity: string,
  targetCandidates: string[],
  topK = 5
): Promise<GNNPredictLinksResponse> {
  const res = await apiClient.post<GNNPredictLinksResponse>("/api/v1/graph/predict-links", {
    source_entity: sourceEntity,
    target_candidates: targetCandidates,
    top_k: topK,
  });
  return res.data;
}

