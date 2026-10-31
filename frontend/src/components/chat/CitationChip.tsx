import React, { useState } from "react";
import { CitationBadge } from "../../types/api";
import { useUIStore } from "../../store/useUIStore";
import { BookOpen } from "lucide-react";

interface CitationChipProps {
  tag: string; // e.g. "[1]"
  citation?: CitationBadge;
  allCitations?: CitationBadge[];
}

export function CitationChip({ tag, citation, allCitations }: CitationChipProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const { openSourcesPanel } = useUIStore();

  // Find matching badge if not passed directly with resilient matching
  const badge =
    citation ||
    allCitations?.find((c) => {
      const cleanTag = tag.replace(/[[\]]/g, "").trim().toLowerCase();
      const cTag = (c.citation_tag || "").replace(/[[\]]/g, "").trim().toLowerCase();
      return (
        cTag === cleanTag ||
        cleanTag.includes(cTag) ||
        cTag.includes(cleanTag) ||
        (c.paper_title && cleanTag.includes(c.paper_title.toLowerCase()))
      );
    }) ||
    allCitations?.[0];

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    openSourcesPanel(undefined, tag, "papers");
  };

  return (
    <span className="relative inline-block align-baseline mx-0.5">
      <button
        type="button"
        onClick={handleClick}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className="inline-flex items-center justify-center px-1.5 py-0.2 text-[11px] font-mono font-medium text-parchment-secondary hover:text-parchment-primary bg-parchment-container-high hover:bg-parchment-secondary-container dark:bg-darkpaper-container dark:hover:bg-darkpaper-container-high border border-parchment-outline-variant cursor-pointer transition-colors"
        title="View grounded citation"
      >
        {tag}
      </button>

      {showTooltip && badge && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 w-72 p-3 bg-parchment-container-lowest dark:bg-darkpaper-surface border border-parchment-outline-variant dark:border-darkpaper-outline shadow-lg z-40 text-left pointer-events-none">
          <div className="flex items-center gap-1.5 text-[10px] font-mono tracking-label uppercase text-parchment-secondary">
            <BookOpen className="w-3 h-3" />
            <span>Citation {badge.citation_tag}</span>
            {badge.page_number && <span>• Page {badge.page_number}</span>}
          </div>
          <div className="mt-1 font-serif font-medium text-xs text-parchment-on-surface dark:text-darkpaper-on-surface line-clamp-2">
            {badge.paper_title}
          </div>
          {badge.section_name && (
            <div className="text-[11px] text-parchment-on-surface-variant italic mt-0.5">
              Section: {badge.section_name}
            </div>
          )}
          {badge.snippet && (
            <div className="mt-1.5 text-[11px] text-parchment-on-surface-variant line-clamp-3 border-l-2 border-parchment-outline-variant pl-2">
              "{badge.snippet}"
            </div>
          )}
          <div className="mt-2 text-[10px] font-mono text-parchment-outline text-right">
            Click to inspect source passage $\rightarrow$
          </div>
        </div>
      )}
    </span>
  );
}

