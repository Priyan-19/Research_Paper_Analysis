import { apiClient } from "./client";
import {
  PaperListResponse,
  PaperDetailResponse,
  PaperResponse,
  ChunkListResponse,
} from "../types/api";

export async function fetchPapers(skip = 0, limit = 50): Promise<PaperListResponse> {
  const res = await apiClient.get<PaperListResponse>("/api/v1/papers", {
    params: { skip, limit },
  });
  return res.data;
}

export async function fetchPaperDetails(paperId: string): Promise<PaperDetailResponse> {
  const res = await apiClient.get<PaperDetailResponse>(`/api/v1/papers/${paperId}`);
  return res.data;
}

export async function fetchPaperChunks(paperId: string): Promise<ChunkListResponse> {
  const res = await apiClient.get<ChunkListResponse>(`/api/v1/papers/${paperId}/chunks`);
  return res.data;
}

export async function uploadPaperPdf(
  file: File,
  onProgress?: (percent: number) => void
): Promise<PaperResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await apiClient.post<PaperResponse>("/api/v1/papers/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });
  return res.data;
}

export async function deletePaper(paperId: string): Promise<void> {
  await apiClient.delete(`/api/v1/papers/${paperId}`);
}

export async function embedPaperChunks(paperId: string): Promise<{ chunks_embedded: number }> {
  const res = await apiClient.post<{ chunks_embedded: number }>(`/api/v1/papers/${paperId}/embed`);
  return res.data;
}

