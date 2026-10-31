import React from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "../../lib/utils";

export type EntityChipType = "CONCEPT" | "METHOD" | "DATASET" | "MODEL" | "AUTHOR" | "TASK" | "METRIC";

interface EntityChipProps {
  name: string;
  type?: EntityChipType | string;
  className?: string;
}

export function EntityChip({ name, type = "CONCEPT", className }: EntityChipProps) {
  const navigate = useNavigate();

  const typeConfig: Record<string, { bg: string; text: string; border: string }> = {
    CONCEPT: { bg: "bg-[#f1ede4]", text: "text-[#3a3531]", border: "border-[#cfc5bd]" },
    METHOD: { bg: "bg-[#e8edf2]", text: "text-[#1d3557]", border: "border-[#b8c9dc]" },
    DATASET: { bg: "bg-[#f4ead9]", text: "text-[#704214]", border: "border-[#dec8a8]" },
    MODEL: { bg: "bg-[#e7f0ea]", text: "text-[#1c4b27]", border: "border-[#b7d5be]" },
    AUTHOR: { bg: "bg-[#ede8f5]", text: "text-[#432874]", border: "border-[#cbb9e2]" },
    METRIC: { bg: "bg-[#faebeb]", text: "text-[#7a1c1c]", border: "border-[#e8b5b5]" },
  };

  const current = typeConfig[type.toUpperCase()] || typeConfig.CONCEPT;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Navigate to Knowledge Graph page with search query
    navigate(`/graph?search=${encodeURIComponent(name)}`);
  };

  return (
    <button
      onClick={handleClick}
      className={cn(
        "inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-serif border hover:opacity-85 transition-opacity cursor-pointer select-none",
        current.bg,
        current.text,
        current.border,
        className
      )}
      title={`Entity: ${name} (${type}) - Click to explore in Knowledge Graph`}
    >
      <span>{name}</span>
      <span className="text-[9px] font-mono tracking-wider opacity-60 uppercase">
        {type.slice(0, 3)}
      </span>
    </button>
  );
}

