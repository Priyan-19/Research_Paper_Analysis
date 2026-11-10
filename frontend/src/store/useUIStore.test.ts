import { describe, it, expect } from "vitest";
import { useUIStore } from "./useUIStore";

describe("useUIStore", () => {
  it("toggles sidebar visibility correctly", () => {
    const initial = useUIStore.getState().isSidebarOpen;
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().isSidebarOpen).toBe(!initial);
    useUIStore.getState().setSidebarOpen(true);
    expect(useUIStore.getState().isSidebarOpen).toBe(true);
  });

  it("opens and closes sources panel with highlighted citation tag", () => {
    const mockSources = [
      {
        source_index: 1,
        paper_id: "paper_001",
        paper_title: "Attention Paper",
        page_number: 2,
        section_name: "Introduction",
        text: "Self-attention overview",
      },
    ];

    useUIStore.getState().openSourcesPanel(mockSources, "[Paper: paper_001, Page: 2]", "papers");

    let state = useUIStore.getState();
    expect(state.isSourcesPanelOpen).toBe(true);
    expect(state.highlightedCitationTag).toBe("[Paper: paper_001, Page: 2]");
    expect(state.activeSourcesList).toHaveLength(1);
    expect(state.activeSourceTab).toBe("papers");

    useUIStore.getState().closeSourcesPanel();
    state = useUIStore.getState();
    expect(state.isSourcesPanelOpen).toBe(false);
    expect(state.highlightedCitationTag).toBeNull();
  });

  it("handles toast notifications creation and dismissal", () => {
    useUIStore.getState().showToast("Test success notification", "success");
    const toasts = useUIStore.getState().toasts;
    expect(toasts.length).toBeGreaterThan(0);
    const lastToast = toasts[toasts.length - 1];
    expect(lastToast.message).toBe("Test success notification");
    expect(lastToast.type).toBe("success");

    useUIStore.getState().dismissToast(lastToast.id);
    expect(useUIStore.getState().toasts.some((t) => t.id === lastToast.id)).toBe(false);
  });
});

