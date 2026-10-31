import { apiClient } from "./client";
import {
  ChatRequest,
  ChatResponse,
  VectorRAGResponse,
} from "../types/api";

export async function sendChatQuery(request: ChatRequest): Promise<ChatResponse> {
  const res = await apiClient.post<ChatResponse>("/api/v1/chat", request);
  return res.data;
}

export async function sendVectorRAGQuery(
  query: string,
  topK = 5,
  paperId?: string | null
): Promise<VectorRAGResponse> {
  const res = await apiClient.post<VectorRAGResponse>("/api/v1/rag/vector", {
    query,
    top_k: topK,
    paper_id: paperId || null,
  });
  return res.data;
}

