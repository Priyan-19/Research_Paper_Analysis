import { describe, it, expect, beforeEach } from "vitest";
import { useSettingsStore, applyThemeClass } from "./useSettingsStore";

describe("useSettingsStore", () => {
  beforeEach(() => {
    useSettingsStore.getState().resetDefaults();
  });

  it("initializes with expected default values", () => {
    const state = useSettingsStore.getState();
    expect(state.llmProvider).toBe("groq");
    expect(state.modelName).toBe("openai/gpt-oss-120b");
    expect(state.theme).toBe("light");
    expect(state.topK).toBe(5);
    expect(state.temperature).toBe(0.2);
  });

  it("updates LLM provider and model name", () => {
    useSettingsStore.getState().setLLMProvider("gemini");
    useSettingsStore.getState().setModelName("gemini-1.5-flash");

    const state = useSettingsStore.getState();
    expect(state.llmProvider).toBe("gemini");
    expect(state.modelName).toBe("gemini-1.5-flash");
  });

  it("updates topK and temperature parameters", () => {
    useSettingsStore.getState().setTopK(10);
    useSettingsStore.getState().setTemperature(0.7);

    const state = useSettingsStore.getState();
    expect(state.topK).toBe(10);
    expect(state.temperature).toBe(0.7);
  });

  it("applies theme classes to document element", () => {
    applyThemeClass("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    applyThemeClass("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});

