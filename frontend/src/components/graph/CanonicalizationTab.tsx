import { useQuery } from "@tanstack/react-query";
import { fetchGraphStats } from "../../api/graph";
import { fetchPapers } from "../../api/papers";
import { useNavigate } from "react-router-dom";
import { GitMerge, Layers, Database, Sparkles, BookOpen } from "lucide-react";
import { GraphStatsResponse, PaperListResponse } from "../../types/api";

export function CanonicalizationTab() {
  const navigate = useNavigate();

  // Query live papers
  const { data: papersData } = useQuery<PaperListResponse>({
    queryKey: ["papers-list"],
    queryFn: () => fetchPapers(0, 10),
  });

  // Query live Neo4j canonical stats
  const { data: statsData, isLoading } = useQuery<GraphStatsResponse>({
    queryKey: ["graph-stats"],
    queryFn: fetchGraphStats,
  });

  const hasNoData = !statsData || statsData.total_nodes === 0;

  return (
    <div className="space-y-4 p-4 font-serif">
      {/* Informative Header Banner */}
      <div className="p-3 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 text-xs text-amber-900 dark:text-amber-300 leading-relaxed">
        <div className="font-semibold flex items-center gap-1.5 mb-0.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-700" />
          <span>Automated Entity Canonicalization Engine</span>
        </div>
        During PDF ingestion, the backend <code className="font-mono px-1 py-0.5 bg-amber-100 dark:bg-amber-900 border border-amber-300">app.graph.canonicalizer.EntityCanonicalizer</code> automatically detects and merges surface form variations (synonyms, acronyms, and aliases) into unified canonical nodes to build a connected Neo4j knowledge graph.
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-xs text-parchment-secondary border border-parchment-outline-variant">
          Querying Neo4j canonical index...
        </div>
      ) : hasNoData ? (
        <div className="p-12 text-center border border-dashed border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container-low text-parchment-on-surface-variant text-sm select-none">
          <GitMerge className="w-10 h-10 mx-auto mb-3 text-parchment-secondary opacity-60" />
          <h4 className="font-serif text-base font-medium text-parchment-primary dark:text-darkpaper-primary mb-1">
            No Canonical Entities Extracted Yet
          </h4>
          <p className="text-xs text-parchment-secondary max-w-md mx-auto mb-4 leading-relaxed font-serif">
            The Neo4j database currently contains 0 nodes. Ingest research PDFs in the Research Papers tab to execute automated entity canonicalization and extract knowledge triples.
          </p>
          <button
            onClick={() => navigate("/papers")}
            className="px-4 py-2 bg-parchment-primary text-parchment-on-primary hover:bg-parchment-primary-container text-xs font-serif transition-colors cursor-pointer"
          >
            Go to Research Papers →
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Real Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-4 border border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container">
              <span className="text-[10px] font-mono tracking-label uppercase text-parchment-secondary block">
                Canonical Entities in Neo4j
              </span>
              <div className="text-2xl font-serif text-parchment-primary mt-1 font-semibold">
                {statsData.total_nodes}
              </div>
              <span className="text-[11px] text-parchment-secondary mt-0.5 block font-serif">
                Unified knowledge nodes
              </span>
            </div>

            <div className="p-4 border border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container">
              <span className="text-[10px] font-mono tracking-label uppercase text-parchment-secondary block">
                Canonical Triples / Edges
              </span>
              <div className="text-2xl font-serif text-parchment-primary mt-1 font-semibold">
                {statsData.total_relationships}
              </div>
              <span className="text-[11px] text-parchment-secondary mt-0.5 block font-serif">
                Multi-hop relational edges
              </span>
            </div>

            <div className="p-4 border border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container">
              <span className="text-[10px] font-mono tracking-label uppercase text-parchment-secondary block">
                Ingested PDF Corpus
              </span>
              <div className="text-2xl font-serif text-parchment-primary mt-1 font-semibold">
                {papersData?.total || 0} Papers
              </div>
              <span className="text-[11px] text-parchment-secondary mt-0.5 block font-serif">
                Source research documents
              </span>
            </div>
          </div>

          {/* Real Entity Types Breakdown */}
          {statsData.entity_type_counts && Object.keys(statsData.entity_type_counts).length > 0 && (
            <div className="p-4 border border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container">
              <div className="flex items-center gap-2 mb-3">
                <Database className="w-4 h-4 text-parchment-secondary" />
                <h4 className="font-serif text-sm font-semibold text-parchment-primary">
                  Canonical Entity Type Distribution
                </h4>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {Object.entries(statsData.entity_type_counts).map(([type, count]) => (
                  <div
                    key={type}
                    className="p-2.5 border border-parchment-outline-variant/60 bg-parchment-container/40 flex items-center justify-between text-xs"
                  >
                    <span className="font-mono text-[11px] uppercase text-parchment-primary">
                      {type}
                    </span>
                    <span className="font-mono text-[11px] text-parchment-secondary font-semibold">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Real Relationship Types Breakdown */}
          {statsData.relationship_type_counts && Object.keys(statsData.relationship_type_counts).length > 0 && (
            <div className="p-4 border border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container">
              <div className="flex items-center gap-2 mb-3">
                <Layers className="w-4 h-4 text-parchment-secondary" />
                <h4 className="font-serif text-sm font-semibold text-parchment-primary">
                  Canonical Relationship Types
                </h4>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {Object.entries(statsData.relationship_type_counts).map(([relType, count]) => (
                  <div
                    key={relType}
                    className="p-2.5 border border-parchment-outline-variant/60 bg-parchment-container/40 flex items-center justify-between text-xs"
                  >
                    <span className="font-mono text-[11px] uppercase text-parchment-primary">
                      {relType}
                    </span>
                    <span className="font-mono text-[11px] text-parchment-secondary font-semibold">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
