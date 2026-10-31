import { create } from "zustand";
import { RetrievedSource } from "../types/chat";

export interface ToastMessage {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

interface UIState {
  isSidebarOpen: boolean;
  isSourcesPanelOpen: boolean;
  activeSourceTab: "papers" | "graph";
  highlightedCitationTag: string | null;
  activeSourcesList: RetrievedSource[];
  toasts: ToastMessage[];

  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  openSourcesPanel: (
    sources?: RetrievedSource[],
    highlightCitationTag?: string | null,
    tab?: "papers" | "graph"
  ) => void;
  closeSourcesPanel: () => void;
  setActiveSourceTab: (tab: "papers" | "graph") => void;
  setHighlightedCitationTag: (tag: string | null) => void;
  showToast: (message: string, type?: "success" | "error" | "info") => void;
  dismissToast: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: true,
  isSourcesPanelOpen: false,
  activeSourceTab: "papers",
  highlightedCitationTag: null,
  activeSourcesList: [],
  toasts: [],

  toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),
  setSidebarOpen: (open) => set({ isSidebarOpen: open }),

  openSourcesPanel: (sources, highlightCitationTag = null, tab = "papers") =>
    set((s) => ({
      isSourcesPanelOpen: true,
      activeSourcesList: sources || s.activeSourcesList,
      highlightedCitationTag: highlightCitationTag,
      activeSourceTab: tab,
    })),

  closeSourcesPanel: () =>
    set({
      isSourcesPanelOpen: false,
      highlightedCitationTag: null,
    }),

  setActiveSourceTab: (tab) => set({ activeSourceTab: tab }),
  setHighlightedCitationTag: (tag) => set({ highlightedCitationTag: tag }),

  showToast: (message, type = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    set((s) => ({
      toasts: [...s.toasts, { id, message, type }],
    }));
    setTimeout(() => {
      set((s) => ({
        toasts: s.toasts.filter((t) => t.id !== id),
      }));
    }, 4500);
  },

  dismissToast: (id) =>
    set((s) => ({
      toasts: s.toasts.filter((t) => t.id !== id),
    })),
}));

