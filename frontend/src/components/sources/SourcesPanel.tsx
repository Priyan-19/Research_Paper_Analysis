import { useEffect } from "react";
import { useUIStore } from "../../store/useUIStore";
import { PapersTab } from "./PapersTab";
import { GraphTab } from "./GraphTab";
import { X, BookOpen, Network } from "lucide-react";
import { cn } from "../../lib/utils";

export function SourcesPanel() {
  const {
    isSourcesPanelOpen,
    closeSourcesPanel,
    activeSourceTab,
    setActiveSourceTab,
    activeSourcesList,
    highlightedCitationTag,
  } = useUIStore();

  // Scroll to highlighted citation source element if requested
  useEffect(() => {
    if (isSourcesPanelOpen && highlightedCitationTag) {
      const cleanNum = highlightedCitationTag.replace(/[[\]]/g, "");
      const el = document.getElementById(`source-${cleanNum}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [isSourcesPanelOpen, highlightedCitationTag]);

  if (!isSourcesPanelOpen) return null;

  return (
    <aside className="w-full sm:w-96 lg:w-[420px] flex-shrink-0 border-l border-parchment-outline-variant bg-parchment-surface dark:bg-darkpaper-surface flex flex-col h-full z-20 shadow-lg sm:shadow-none">
      {/* Panel Header */}
      <div className="flex items-center justify-between p-3.5 border-b border-parchment-outline-variant bg-parchment-container-low dark:bg-darkpaper-container">
        <div>
          <h3 className="font-serif text-sm font-medium text-parchment-on-surface dark:text-darkpaper-on-surface">
            Evidence & Source Inspector
          </h3>
          <span className="text-[10px] font-mono tracking-label uppercase text-parchment-secondary">
            {activeSourcesList.length} Grounded Source Items
          </span>
        </div>

        <button
          onClick={closeSourcesPanel}
          className="p-1 text-parchment-secondary hover:text-parchment-primary hover:bg-parchment-container transition-colors"
          title="Close panel (Esc)"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-parchment-outline-variant text-xs font-serif bg-parchment-container-lowest dark:bg-darkpaper-surface">
        <button
          onClick={() => setActiveSourceTab("papers")}
          className={cn(
            "flex-1 py-2.5 px-3 flex items-center justify-center gap-1.5 transition-colors border-r border-parchment-outline-variant",
            activeSourceTab === "papers"
              ? "bg-parchment-surface font-medium text-parchment-primary border-b-2 border-b-parchment-primary dark:bg-darkpaper-surface dark:border-b-darkpaper-primary"
              : "text-parchment-on-surface-variant hover:bg-parchment-container/50"
          )}
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span>Papers Chunks</span>
        </button>

        <button
          onClick={() => setActiveSourceTab("graph")}
          className={cn(
            "flex-1 py-2.5 px-3 flex items-center justify-center gap-1.5 transition-colors",
            activeSourceTab === "graph"
              ? "bg-parchment-surface font-medium text-parchment-primary border-b-2 border-b-parchment-primary dark:bg-darkpaper-surface dark:border-b-darkpaper-primary"
              : "text-parchment-on-surface-variant hover:bg-parchment-container/50"
          )}
        >
          <Network className="w-3.5 h-3.5" />
          <span>Knowledge Graph</span>
        </button>
      </div>

      {/* Tab Body */}
      <div className="flex-1 overflow-y-auto">
        {activeSourceTab === "papers" ? (
          <PapersTab sources={activeSourcesList} highlightTag={highlightedCitationTag} />
        ) : (
          <GraphTab sources={activeSourcesList} highlightTag={highlightedCitationTag} />
        )}
      </div>
    </aside>
  );
}

