import { apiClient } from "./client";
import { SystemHealthResponse } from "../types/api";

export async function fetchHealth(): Promise<SystemHealthResponse> {
  const res = await apiClient.get<SystemHealthResponse>("/api/v1/health");
  return res.data;
}

