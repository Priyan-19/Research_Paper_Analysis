import React, { useState, useRef, useEffect } from "react";
import { useUIStore } from "../../store/useUIStore";
import { useChatStore } from "../../store/useChatStore";
import {
  PanelLeft,
  PanelRight,
  Sparkles,
  SquarePen,
  ChevronDown,
  Check,
  Layers,
  Network,
  Binary
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { SearchMode } from "../../types/api";
import { cn } from "../../lib/utils";

export function Header() {
  const { isSidebarOpen, toggleSidebar, isSourcesPanelOpen, openSourcesPanel, closeSourcesPanel, activeSourcesList } = useUIStore();
  const { conversations, activeConversationId, searchMode, setSearchMode, createConversation, selectConversation } = useChatStore();
  const navigate = useNavigate();

  const [isModeDropdownOpen, setIsModeDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentConv = conversations.find((c) => c.id === activeConversationId);
  const activeTitle = currentConv?.title || "New Research Inquiry";

  const handleQuickNewChat = () => {
    const id = createConversation();
    selectConversation(id);
    navigate("/chat");
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsModeDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const modeOptions: { id: SearchMode; label: string; desc: string; icon: React.ElementType }[] = [
    {
      id: "hybrid",
      label: "Hybrid RAG",
      desc: "PostgreSQL pgvector + Neo4j with Reciprocal Rank Fusion",
      icon: Layers,
    },
    {
      id: "vector",
      label: "Vector Semantic",
      desc: "Dense embedding cosine similarity over PDF chunks",
      icon: Binary,
    },
    {
      id: "graph",
      label: "Graph Traversal",
      desc: "Neo4j multi-hop entity, author & concept reasoning",
      icon: Network,
    },
  ];

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

      {/* Right: Retrieval Mode Dropdown Pill + Sources Drawer Button */}
      <div className="flex items-center gap-2.5 flex-shrink-0">
        {/* Interactive Mode Selector Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setIsModeDropdownOpen(!isModeDropdownOpen)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-serif text-parchment-primary dark:text-darkpaper-primary bg-parchment-container/50 hover:bg-parchment-container dark:bg-darkpaper-container dark:hover:bg-darkpaper-container-high border border-parchment-outline-variant/60 transition-colors cursor-pointer"
            title="Change Retrieval Strategy"
          >
            <Sparkles className="w-3 h-3 text-parchment-secondary flex-shrink-0" />
            <span className="capitalize font-medium">{searchMode} RAG</span>
            <ChevronDown className="w-3 h-3 text-parchment-secondary ml-0.5" />
          </button>

          {isModeDropdownOpen && (
            <div className="absolute right-0 mt-1.5 w-64 bg-parchment-container-lowest dark:bg-darkpaper-container border border-parchment-outline-variant shadow-lg py-1 z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="px-3 py-1.5 border-b border-parchment-outline-variant/40 text-[10px] font-mono tracking-label uppercase text-parchment-secondary">
                Retrieval Strategy
              </div>
              {modeOptions.map((opt) => {
                const Icon = opt.icon;
                const isSelected = searchMode === opt.id;
                return (
                  <button
                    key={opt.id}
                    onClick={() => {
                      setSearchMode(opt.id);
                      setIsModeDropdownOpen(false);
                    }}
                    className={cn(
                      "w-full px-3 py-2 text-left flex items-start gap-2.5 hover:bg-parchment-container dark:hover:bg-darkpaper-container-high transition-colors cursor-pointer",
                      isSelected && "bg-parchment-container/60 dark:bg-darkpaper-container-high"
                    )}
                  >
                    <Icon className="w-4 h-4 text-parchment-secondary mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-serif text-xs font-medium text-parchment-primary dark:text-darkpaper-primary">
                          {opt.label}
                        </span>
                        {isSelected && <Check className="w-3.5 h-3.5 text-parchment-primary dark:text-darkpaper-primary" />}
                      </div>
                      <p className="font-serif text-[11px] text-parchment-secondary leading-snug mt-0.5">
                        {opt.desc}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Evidence Sources Button with Count Badge */}
        <button
          onClick={() => (isSourcesPanelOpen ? closeSourcesPanel() : openSourcesPanel())}
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
          {activeSourcesList.length > 0 && (
            <span
              className={cn(
                "font-mono text-[10px] px-1.5 py-0.2",
                isSourcesPanelOpen
                  ? "bg-white/20 text-white"
                  : "bg-parchment-secondary-container text-parchment-on-secondary-container font-medium"
              )}
            >
              {activeSourcesList.length}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
