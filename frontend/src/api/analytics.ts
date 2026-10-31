import { apiClient } from "./client";
import { TrendOverviewResponse, EvaluationReportResponse } from "../types/api";

export async function fetchTrendsOverview(): Promise<TrendOverviewResponse> {
  const res = await apiClient.get<TrendOverviewResponse>("/api/v1/trends/overview");
  return res.data;
}

export async function fetchEvaluationResults(): Promise<EvaluationReportResponse> {
  const res = await apiClient.get<EvaluationReportResponse>("/api/v1/evaluation/results");
  return res.data;
}

export async function recommendCitations(
  statement: string,
  topK = 5
): Promise<{
  statement: string;
  recommended_papers: Array<{
    paper_id: string;
    paper_title: string;
    similarity_score: number;
    recommended_reason: string;
  }>;
}> {
  const res = await apiClient.post("/api/v1/citations/recommend", {
    statement,
    top_k: topK,
  });
  return res.data;
}

export async function checkPaperSimilarity(
  sourcePaperId: string,
  targetPaperId?: string
): Promise<any> {
  const res = await apiClient.post("/api/v1/similarity/check", {
    source_paper_id: sourcePaperId,
    target_paper_id: targetPaperId || null,
  });
  return res.data;
}

