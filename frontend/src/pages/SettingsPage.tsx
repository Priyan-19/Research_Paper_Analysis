import { useState } from "react";
import { useSettingsStore, ThemeMode } from "../store/useSettingsStore";
import { useChatStore } from "../store/useChatStore";
import { useUIStore } from "../store/useUIStore";
import { fetchHealth } from "../api/health";
import { SystemHealthResponse } from "../types/api";
import { useQuery } from "@tanstack/react-query";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Sliders, Sun, Moon, Laptop, Trash2, RefreshCw, Cpu, Database } from "lucide-react";

export function SettingsPage() {
  const {
    apiBaseUrl,
    setApiBaseUrl,
    llmProvider,
    setLLMProvider,
    modelName,
    setModelName,
    theme,
    setTheme,
    topK,
    setTopK,
    temperature,
    setTemperature,
    resetDefaults,
  } = useSettingsStore();

  const { clearAllConversations } = useChatStore();
  const { showToast } = useUIStore();

  const [inputUrl, setInputUrl] = useState(apiBaseUrl);

  // Health check query
  const { data: healthData, isError, refetch, isFetching } = useQuery<SystemHealthResponse>({
    queryKey: ["backend-health"],
    queryFn: fetchHealth,
    retry: 1,
  });

  const handleSaveApiUrl = () => {
    if (inputUrl.trim()) {
      setApiBaseUrl(inputUrl.trim());
      showToast("Updated API Base URL. Checking connection...", "info");
      refetch();
    }
  };

  const handleProviderSelect = (providerId: string, defaultModel: string) => {
    setLLMProvider(providerId);
    setModelName(defaultModel);
    showToast(`Switched active provider to ${providerId}.`, "success");
  };

  const handleClearHistory = () => {
    if (confirm("Are you sure you want to clear all conversation dialogues and search history?")) {
      clearAllConversations();
      showToast("Conversation history cleared from local storage.", "info");
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-8 max-w-4xl mx-auto w-full space-y-8 font-serif">
      {/* Header */}
      <div className="border-b border-parchment-outline-variant pb-4">
        <span className="text-[10px] font-mono tracking-label-wide uppercase text-parchment-secondary block">
          Configuration & Environment
        </span>
        <h1 className="text-2xl sm:text-3xl font-normal text-parchment-on-surface dark:text-darkpaper-on-surface">
          System Preferences & LLM Setup
        </h1>
        <p className="text-sm text-parchment-on-surface-variant mt-1">
          Configure API endpoints, choose Large Language Model inference engines, calibrate retrieval Top-K parameters, and manage local storage.
        </p>
      </div>

      {/* Section 1: API Base URL & Connectivity */}
      <section className="space-y-4">
        <h3 className="font-serif text-base font-medium text-parchment-on-surface dark:text-darkpaper-on-surface flex items-center gap-2">
          <Database className="w-4 h-4 text-parchment-secondary" />
          <span>FastAPI Backend Connection</span>
        </h3>

        <Card>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-mono tracking-label uppercase text-parchment-secondary block mb-1">
                FastAPI REST Endpoint URL
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={inputUrl}
                  onChange={(e) => setInputUrl(e.target.value)}
                  className="flex-1 p-2 text-xs font-mono bg-parchment-container border border-parchment-outline-variant outline-none focus:border-parchment-primary"
                  placeholder="http://127.0.0.1:8000"
                />
                <Button size="sm" variant="primary" onClick={handleSaveApiUrl}>
                  Save & Connect
                </Button>
                <Button size="sm" variant="outline" onClick={() => refetch()} disabled={isFetching}>
                  <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />
                </Button>
              </div>
            </div>

            {/* Connection Status Banner */}
            <div className="p-3 border text-xs font-mono flex items-center justify-between bg-parchment-container/50 border-parchment-outline-variant">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    !isError && healthData?.status === "healthy" ? "bg-emerald-500" : "bg-rose-500"
                  }`}
                />
                <span className="font-semibold text-parchment-on-surface">
                  {!isError && healthData?.status === "healthy" ? "Backend Connected & Healthy" : "Backend Offline / Degraded"}
                </span>
              </div>

              {healthData?.services && (
                <div className="flex items-center gap-2 text-[10px] text-parchment-secondary">
                  <span>PostgreSQL: {healthData.services.postgresql?.connected ? "✓" : "✗"}</span>
                  <span>Neo4j: {healthData.services.neo4j?.connected ? "✓" : "✗"}</span>
                  <span>Redis: {healthData.services.redis?.connected ? "✓" : "✗"}</span>
                </div>
              )}
            </div>
          </div>
        </Card>
      </section>

      {/* Section 2: LLM Configuration */}
      <section className="space-y-4">
        <h3 className="font-serif text-base font-medium text-parchment-on-surface dark:text-darkpaper-on-surface flex items-center gap-2">
          <Cpu className="w-4 h-4 text-parchment-secondary" />
          <span>Large Language Model Reasoning Engine</span>
        </h3>

        <div className="p-4 border border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container">
          <h4 className="font-serif text-sm font-semibold text-parchment-primary dark:text-darkpaper-primary">
            Groq Cloud (Llama-3.3 / GPT-OSS)
          </h4>
        </div>

        <Card>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-mono tracking-label uppercase text-parchment-secondary block mb-1">
                Top-K Retrieved Evidence Items ({topK})
              </label>
              <input
                type="range"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full accent-parchment-primary"
              />
              <span className="text-[11px] text-parchment-outline">
                Number of vector passages and graph triples retrieved per query.
              </span>
            </div>

            <div>
              <label className="text-xs font-mono tracking-label uppercase text-parchment-secondary block mb-1">
                LLM Temperature ({temperature})
              </label>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full accent-parchment-primary"
              />
              <span className="text-[11px] text-parchment-outline">
                Lower values (0.1 - 0.2) ensure deterministic grounded research citations.
              </span>
            </div>
          </div>
        </Card>
      </section>

      {/* Section 3: Interface Theme & Local Storage */}
      <section className="space-y-4">
        <h3 className="font-serif text-base font-medium text-parchment-on-surface dark:text-darkpaper-on-surface flex items-center gap-2">
          <Sliders className="w-4 h-4 text-parchment-secondary" />
          <span>Interface Appearance & Storage</span>
        </h3>

        <Card>
          <div className="space-y-4">
            <div>
              <label className="text-xs font-mono tracking-label uppercase text-parchment-secondary block mb-2">
                Design Theme Mode
              </label>
              <div className="inline-flex border border-parchment-outline-variant text-xs font-serif">
                {(["light", "dark", "system"] as ThemeMode[]).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setTheme(mode)}
                    className={`px-4 py-2 capitalize transition-colors flex items-center gap-1.5 ${
                      theme === mode
                        ? "bg-parchment-primary text-parchment-on-primary font-medium dark:bg-darkpaper-primary dark:text-darkpaper-on-primary"
                        : "text-parchment-on-surface-variant hover:bg-parchment-container"
                    }`}
                  >
                    {mode === "light" && <Sun className="w-3.5 h-3.5" />}
                    {mode === "dark" && <Moon className="w-3.5 h-3.5" />}
                    {mode === "system" && <Laptop className="w-3.5 h-3.5" />}
                    <span>{mode}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-parchment-outline-variant flex items-center justify-between">
              <div>
                <h5 className="font-serif text-sm font-medium text-parchment-on-surface">
                  Clear Local Conversation History
                </h5>
                <p className="text-xs text-parchment-on-surface-variant">
                  Removes all saved dialogues, pinned research inquiries, and temporary caches from browser memory.
                </p>
              </div>

              <Button variant="danger" size="sm" onClick={handleClearHistory}>
                <Trash2 className="w-3.5 h-3.5 mr-1" />
                <span>Clear History</span>
              </Button>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
