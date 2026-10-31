import axios from "axios";

export const DEFAULT_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function getApiBaseUrl(): string {
  try {
    const saved = localStorage.getItem("rag_api_base_url");
    if (saved) return saved;
  } catch (e) {
    // ignore
  }
  return DEFAULT_API_BASE_URL;
}

export function setApiBaseUrl(url: string): void {
  try {
    localStorage.setItem("rag_api_base_url", url);
  } catch (e) {
    // ignore
  }
}

export const apiClient = axios.create({
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  config.baseURL = getApiBaseUrl();
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = "Network error. Please ensure the FastAPI backend is running.";
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (typeof detail === "string") {
        message = detail;
      } else if (detail.message) {
        message = `${detail.error ? detail.error + ": " : ""}${detail.message}`;
      } else {
        message = JSON.stringify(detail);
      }
    } else if (error.message) {
      message = error.message;
    }
    return Promise.reject(new Error(message));
  }
);

