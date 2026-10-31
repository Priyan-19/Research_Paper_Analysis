import { create } from "zustand";
import { persist } from "zustand/middleware";
import { setApiBaseUrl as persistApiBaseUrl, getApiBaseUrl } from "../api/client";

export type ThemeMode = "light" | "dark" | "system";

interface SettingsState {
  apiBaseUrl: string;
  llmProvider: string;
  modelName: string;
  theme: ThemeMode;
  topK: number;
  temperature: number;
  setApiBaseUrl: (url: string) => void;
  setLLMProvider: (provider: string) => void;
  setModelName: (model: string) => void;
  setTheme: (theme: ThemeMode) => void;
  setTopK: (topK: number) => void;
  setTemperature: (temp: number) => void;
  resetDefaults: () => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      apiBaseUrl: getApiBaseUrl(),
      llmProvider: "groq",
      modelName: "openai/gpt-oss-120b",
      theme: "light",
      topK: 5,
      temperature: 0.2,

      setApiBaseUrl: (url: string) => {
        persistApiBaseUrl(url);
        set({ apiBaseUrl: url });
      },
      setLLMProvider: (provider: string) => set({ llmProvider: provider }),
      setModelName: (model: string) => set({ modelName: model }),
      setTheme: (theme: ThemeMode) => {
        set({ theme });
        applyThemeClass(theme);
      },
      setTopK: (topK: number) => set({ topK }),
      setTemperature: (temp: number) => set({ temperature: temp }),
      resetDefaults: () =>
        set({
          apiBaseUrl: "http://127.0.0.1:8000",
          llmProvider: "groq",
          modelName: "openai/gpt-oss-120b",
          theme: "light",
          topK: 5,
          temperature: 0.2,
        }),
    }),
    {
      name: "rag_research_settings",
    }
  )
);

export function applyThemeClass(theme: ThemeMode) {
  const root = document.documentElement;
  const isDark =
    theme === "dark" ||
    (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);

  if (isDark) {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

