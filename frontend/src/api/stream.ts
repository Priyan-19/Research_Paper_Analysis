import { ChatRequest, ChatResponse } from "../types/api";
import { getApiBaseUrl } from "./client";

export interface StreamChatOptions {
  request: ChatRequest;
  onChunk: (chunk: string, aggregatedText: string) => void;
  onComplete: (response: ChatResponse) => void;
  onError: (error: Error) => void;
}

/**
 * Robust Chat Streaming Client.
 * Supports both true SSE streams (text/event-stream) and simulates smooth
 * typewriter token streaming for synchronous JSON endpoints with AbortController.
 */
export function streamChat({
  request,
  onChunk,
  onComplete,
  onError,
}: StreamChatOptions): AbortController {
  const controller = new AbortController();
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}/api/v1/chat`;

  (async () => {
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream, application/json",
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      if (!response.ok) {
        let errMessage = `Server responded with status ${response.status}`;
        try {
          const errData = await response.json();
          if (errData?.detail) {
            if (typeof errData.detail === "string") {
              errMessage = errData.detail;
            } else if (errData.detail.message) {
              errMessage = `${errData.detail.error ? errData.detail.error + ': ' : ''}${errData.detail.message}`;
            } else {
              errMessage = JSON.stringify(errData.detail);
            }
          }
        } catch {
          // fallback to status text
        }
        throw new Error(errMessage);
      }

      const contentType = response.headers.get("content-type") || "";

      // 1. If backend supports real SSE streaming
      if (contentType.includes("text/event-stream") && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let aggregated = "";
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith("data:")) {
              const dataStr = trimmed.replace(/^data:\s*/, "");
              if (dataStr === "[DONE]") continue;

              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.chunk) {
                  aggregated += parsed.chunk;
                  onChunk(parsed.chunk, aggregated);
                } else if (parsed.answer) {
                  onComplete(parsed as ChatResponse);
                  return;
                }
              } catch {
                aggregated += dataStr;
                onChunk(dataStr, aggregated);
              }
            }
          }
        }

        onComplete({
          query: request.query,
          answer: aggregated,
          search_mode: request.search_mode || "hybrid",
          total_citations: 0,
          citations: [],
          insufficient_evidence: false,
          llm_provider: "stream",
          execution_time_seconds: 0,
        });
        return;
      }

      // 2. Synchronous JSON Endpoint -> Typewriter Streaming Effect
      const data: ChatResponse = await response.json();
      const fullText = data.answer || "";
      const words = fullText.split(/(\s+)/); // preserve spaces

      let aggregated = "";
      for (let i = 0; i < words.length; i++) {
        if (controller.signal.aborted) {
          return;
        }

        const token = words[i];
        aggregated += token;
        onChunk(token, aggregated);

        // Adjust cadence for realistic streaming feel
        const delay = token.endsWith(".") || token.endsWith("\n") ? 32 : 12;
        await new Promise((res) => setTimeout(res, delay));
      }

      if (!controller.signal.aborted) {
        onComplete(data);
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        // Generation stopped by user
        return;
      }
      onError(err instanceof Error ? err : new Error(String(err)));
    }
  })();

  return controller;
}

