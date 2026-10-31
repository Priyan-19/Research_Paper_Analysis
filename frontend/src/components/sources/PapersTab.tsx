import { RetrievedSource } from "../../types/chat";
import { Badge } from "../ui/Badge";
import { BookOpen, FileText, Sparkles } from "lucide-react";

interface PapersTabProps {
  sources: RetrievedSource[];
  highlightTag?: string | null;
}

export function PapersTab({ sources, highlightTag }: PapersTabProps) {
  const paperSources = sources.filter((s) => s.source_type !== "graph");

  if (paperSources.length === 0) {
    return (
      <div className="p-6 text-center text-sm font-serif text-parchment-on-surface-variant">
        <BookOpen className="w-8 h-8 text-parchment-outline mx-auto mb-2 opacity-50" />
        <p>No document text chunks retrieved for this turn.</p>
        <p className="text-xs text-parchment-outline mt-1 font-mono">
          Sources appear when the retrieval mode includes Vector Search or Hybrid RRF.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3.5 p-4 overflow-y-auto">
      {paperSources.map((source, idx) => {
        const isHighlighted =
          highlightTag &&
          (highlightTag === `[${source.source_index}]` ||
            highlightTag === String(source.source_index));

        return (
          <div
            key={source.chunk_id || idx}
            id={`source-${source.source_index}`}
            className={`p-3.5 border transition-all text-left bg-parchment-container-lowest dark:bg-darkpaper-container-low ${
              isHighlighted
                ? "border-parchment-primary ring-1 ring-parchment-primary bg-parchment-secondary-container/20"
                : "border-parchment-outline-variant hover:border-parchment-outline"
            }`}
          >
            {/* Header: Badge & Score */}
            <div className="flex items-center justify-between gap-2 mb-2">
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-xs font-semibold text-parchment-primary">
                  [{source.source_index}]
                </span>
                <Badge variant={source.source_type === "hybrid" ? "hybrid" : "vector"}>
                  {source.source_type === "hybrid" ? "RRF Fused" : "Vector Chunk"}
                </Badge>
              </div>

              {source.score !== undefined && (
                <span className="text-[10px] font-mono text-parchment-secondary flex items-center gap-1">
                  <Sparkles className="w-2.5 h-2.5" />
                  <span>Score: {source.score.toFixed(3)}</span>
                </span>
              )}
            </div>

            {/* Paper Title */}
            <h5 className="font-serif text-sm font-medium text-parchment-on-surface dark:text-darkpaper-on-surface mb-1 flex items-start gap-1.5">
              <FileText className="w-3.5 h-3.5 text-parchment-secondary mt-0.5 flex-shrink-0" />
              <span>{source.paper_title || source.paper_id}</span>
            </h5>

            {/* Page & Section Metadata */}
            <div className="flex flex-wrap items-center gap-x-2 text-[11px] font-serif text-parchment-on-surface-variant mb-2">
              {source.page_number && <span>Page {source.page_number}</span>}
              {source.section_name && <span>• Section: {source.section_name}</span>}
            </div>

            {/* Snippet */}
            <div className="p-2.5 bg-parchment-container/50 dark:bg-darkpaper-container border-l-2 border-parchment-secondary text-xs font-serif leading-relaxed text-parchment-on-surface line-clamp-6">
              "{source.snippet}"
            </div>
          </div>
        );
      })}
    </div>
  );
}

