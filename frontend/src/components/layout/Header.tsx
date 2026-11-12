import React from "react";
import { useUIStore } from "../../store/useUIStore";
import { useChatStore } from "../../store/useChatStore";
import {
  PanelLeft,
  PanelRight,
  Sparkles,
  SquarePen,
  Layers,
  Network
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { cn } from "../../lib/utils";

export function Header() {
  const { isSidebarOpen, toggleSidebar, isSourcesPanelOpen, openSourcesPanel, closeSourcesPanel, activeSourcesList } = useUIStore();
  const { conversations, activeConversationId, createConversation, selectConversation } = useChatStore();
  const navigate = useNavigate();

  const currentConv = conversations.find((c) => c.id === activeConversationId);
  const activeTitle = currentConv?.title || "New Research Inquiry";

  const lastAssistantWithSources = [...(currentConv?.messages || [])]
    .reverse()
    .find((m) => m.role === "assistant" && m.retrieved_sources && m.retrieved_sources.length > 0);

  const displaySourcesCount = activeSourcesList.length > 0
    ? activeSourcesList.length
    : (lastAssistantWithSources?.retrieved_sources?.length || 0);

  const handleToggleSources = () => {
    if (isSourcesPanelOpen) {
      closeSourcesPanel();
    } else {
      const sourcesToOpen = activeSourcesList.length > 0
        ? activeSourcesList
        : (lastAssistantWithSources?.retrieved_sources || []);
      openSourcesPanel(sourcesToOpen);
    }
  };

  const handleQuickNewChat = () => {
    const id = createConversation();
    selectConversation(id);
    navigate("/chat");
  };

  return (
    <header className="h-14 border-b border-parchment-outline-variant/40 bg-parchment-surface/90 dark:bg-darkpaper-surface/90 backdrop-blur-xs px-3 sm:px-5 flex items-center justify-between z-20 flex-shrink-0 transition-colors">
      {/* Left: Sidebar toggle + Quick New Inquiry + Active Dialogue Title */}
      <div className="flex items-center gap-2 min-w-0">
        <button
          onClick={toggleSidebar}
          className="p-2 text-parchment-secondary hover:text-parchment-primary hover:bg-parchment-container/70 dark:hover:bg-darkpaper-container transition-colors cursor-pointer"
          title={isSidebarOpen ? "Collapse Navigation Sidebar" : "Expand Navigation Sidebar"}
          aria-label="Toggle Sidebar"
        >
          <PanelLeft className="w-4 h-4" />
        </button>

        <button
          onClick={handleQuickNewChat}
          className="p-2 text-parchment-secondary hover:text-parchment-primary hover:bg-parchment-container/70 dark:hover:bg-darkpaper-container transition-colors cursor-pointer"
          title="New Research Inquiry (⌘⇧O)"
          aria-label="New Research Inquiry"
        >
          <SquarePen className="w-4 h-4" />
        </button>

        <div className="h-4 w-px bg-parchment-outline-variant/50 mx-1 flex-shrink-0" />

        <div className="flex items-center gap-1.5 min-w-0">
          <span className="font-serif font-medium text-sm text-parchment-primary dark:text-darkpaper-primary truncate max-w-[200px] sm:max-w-xs md:max-w-md">
            {activeTitle}
          </span>
        </div>
      </div>

      {/* Right: Hybrid RAG Fixed Indicator + Sources Drawer Button */}
      <div className="flex items-center gap-2.5 flex-shrink-0">
        {/* Fixed Hybrid Retrieval Mode Indicator */}
        <div
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-serif text-parchment-primary dark:text-darkpaper-primary bg-parchment-container/50 border border-parchment-outline-variant/60"
          title="Unified Hybrid Retrieval: PostgreSQL pgvector + Neo4j Knowledge Graph with RRF"
        >
          <Sparkles className="w-3 h-3 text-parchment-secondary flex-shrink-0" />
          <span className="font-medium">Hybrid RAG</span>
        </div>

        {/* Evidence Sources Button with Count Badge */}
        <button
          onClick={handleToggleSources}
          className={cn(
            "inline-flex items-center gap-2 px-3 py-1 text-xs font-serif border transition-all cursor-pointer",
            isSourcesPanelOpen
              ? "bg-parchment-primary text-parchment-on-primary border-parchment-primary dark:bg-darkpaper-primary dark:text-darkpaper-on-primary font-medium shadow-xs"
              : "text-parchment-secondary hover:text-parchment-primary border-parchment-outline-variant/60 hover:bg-parchment-container dark:hover:bg-darkpaper-container"
          )}
          title="Toggle Grounded Evidence Sources & Citations"
        >
          <PanelRight className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Evidence Sources</span>
          {displaySourcesCount > 0 && (
            <span
              className={cn(
                "font-mono text-[10px] px-1.5 py-0.2",
                isSourcesPanelOpen
                  ? "bg-white/20 text-white"
                  : "bg-parchment-secondary-container text-parchment-on-secondary-container font-medium"
              )}
            >
              {displaySourcesCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
