import { RetrievedSource } from "../../types/chat";
import { Badge } from "../ui/Badge";
import { Network, ArrowRight, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface GraphTabProps {
  sources: RetrievedSource[];
  highlightTag?: string | null;
}

export function GraphTab({ sources }: GraphTabProps) {
  const navigate = useNavigate();
  const graphSources = sources.filter(
    (s) => s.source_type === "graph" || s.relationship || s.source_entity
  );

  if (graphSources.length === 0) {
    return (
      <div className="p-6 text-center text-sm font-serif text-parchment-on-surface-variant">
        <Network className="w-8 h-8 text-parchment-outline mx-auto mb-2 opacity-50" />
        <p>No Neo4j graph triples retrieved for this query.</p>
        <p className="text-xs text-parchment-outline mt-1 font-mono">
          Try switching retrieval mode to "Hybrid" or "Graph" in the composer.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3 p-4 overflow-y-auto">
      {graphSources.map((source, idx) => (
        <div
          key={idx}
          className="p-3.5 border border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container-low text-left hover:border-parchment-outline transition-all"
        >
          <div className="flex items-center justify-between gap-2 mb-2">
            <Badge variant="graph">Neo4j Relational Triple</Badge>
            {source.score !== undefined && (
              <span className="text-[10px] font-mono text-parchment-secondary flex items-center gap-1">
                <Sparkles className="w-2.5 h-2.5" />
                <span>RRF Rank: {source.score.toFixed(3)}</span>
              </span>
            )}
          </div>

          {/* Triple visualization: (Source) -> [RELATION] -> (Target) */}
          <div className="flex items-center flex-wrap gap-2 text-xs font-serif my-2 p-2 bg-parchment-container/50 dark:bg-darkpaper-container border border-dashed border-parchment-outline-variant">
            <span
              onClick={() => navigate(`/graph?search=${encodeURIComponent(source.source_entity || "")}`)}
              className="font-medium text-parchment-primary hover:underline cursor-pointer"
            >
              ({source.source_entity || "Entity"})
            </span>
            <div className="inline-flex items-center gap-1 text-[10px] font-mono uppercase px-1.5 py-0.5 bg-amber-100 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 border border-amber-300">
              <span>{source.relationship || "RELATED_TO"}</span>
              <ArrowRight className="w-2.5 h-2.5" />
            </div>
            <span
              onClick={() => navigate(`/graph?search=${encodeURIComponent(source.target_entity || "")}`)}
              className="font-medium text-parchment-primary hover:underline cursor-pointer"
            >
              ({source.target_entity || "Entity"})
            </span>
          </div>

          {source.snippet && (
            <p className="text-xs font-serif text-parchment-on-surface-variant leading-relaxed mt-2">
              {source.snippet}
            </p>
          )}

          {source.paper_title && (
            <div className="text-[10px] font-mono text-parchment-outline mt-2 pt-1 border-t border-parchment-outline-variant/40">
              Source Paper: {source.paper_title}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

