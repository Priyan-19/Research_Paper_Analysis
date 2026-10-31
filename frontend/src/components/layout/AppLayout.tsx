import { useEffect } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { SourcesPanel } from "../sources/SourcesPanel";
import { ToastContainer } from "../ui/ToastContainer";
import { useChatStore } from "../../store/useChatStore";
import { useUIStore } from "../../store/useUIStore";
import { useSettingsStore, applyThemeClass } from "../../store/useSettingsStore";

export function AppLayout() {
  const navigate = useNavigate();
  const { createConversation, selectConversation, stopStreaming } = useChatStore();
  const { closeSourcesPanel } = useUIStore();
  const { theme } = useSettingsStore();

  // Apply light/dark theme on mount & changes
  useEffect(() => {
    applyThemeClass(theme);
  }, [theme]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // 1. Esc: Stop generation / close sources panel
      if (e.key === "Escape") {
        stopStreaming();
        closeSourcesPanel();
      }

      // 2. Ctrl/Cmd + Shift + O: New Chat
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "o") {
        e.preventDefault();
        const id = createConversation();
        navigate("/chat");
        selectConversation(id);
      }

      // 3. Ctrl/Cmd + K: Focus Search
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        const searchInput = document.querySelector('input[placeholder*="Search"]') as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [createConversation, selectConversation, stopStreaming, closeSourcesPanel, navigate]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-parchment-surface dark:bg-darkpaper-surface text-parchment-on-surface dark:text-darkpaper-on-surface antialiased font-serif">
      {/* Collapsible Left Sidebar */}
      <Sidebar />

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <Header />
        <main className="flex-1 overflow-hidden relative flex">
          <div className="flex-1 flex flex-col h-full overflow-y-auto">
            <Outlet />
          </div>
          {/* Slide-over Right Sources & Evidence Inspector */}
          <SourcesPanel />
        </main>
      </div>

      {/* Toasts */}
      <ToastContainer />
    </div>
  );
}

