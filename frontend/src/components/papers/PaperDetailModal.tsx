import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchPaperDetails } from "../../api/papers";
import { extractPaperGraph, fetchPaperGraph } from "../../api/graph";
import { useUIStore } from "../../store/useUIStore";
import { X, Network, BookOpen, Layers, Loader2, Sparkles } from "lucide-react";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

interface PaperDetailModalProps {
  paperId: string;
  onClose: () => void;
}

export function PaperDetailModal({ paperId, onClose }: PaperDetailModalProps) {
  const queryClient = useQueryClient();
  const { showToast } = useUIStore();
  const [activeTab, setActiveTab] = useState<"metadata" | "chunks" | "graph">("metadata");

  // Fetch Paper Details (metadata + chunks)
  const { data: paper, isLoading } = useQuery({
    queryKey: ["paper-detail", paperId],
    queryFn: () => fetchPaperDetails(paperId),
  });

  // Fetch Paper Graph
  const { data: graphData, refetch: refetchGraph } = useQuery({
    queryKey: ["paper-graph", paperId],
    queryFn: () => fetchPaperGraph(paperId),
    enabled: activeTab === "graph",
  });

  // Extract Knowledge Graph Mutation
  const extractMutation = useMutation({
    mutationFn: () => extractPaperGraph(paperId),
    onSuccess: (res) => {
      showToast(res.message || "Knowledge Graph built in Neo4j!", "success");
      queryClient.invalidateQueries({ queryKey: ["graph-stats"] });
      refetchGraph();
      setActiveTab("graph");
    },
    onError: (err: any) => {
      showToast(err.message || "Failed to extract graph", "error");
    },
  });

  if (isLoading || !paper) {
    return (
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
        <div className="bg-parchment-container-lowest p-6 border border-parchment-outline-variant max-w-md w-full text-center font-serif">
          <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2 text-parchment-primary" />
          <p className="text-sm">Retrieving paper metadata and chunks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
      <div className="bg-parchment-container-lowest dark:bg-darkpaper-surface border border-parchment-outline-variant dark:border-darkpaper-outline max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl">
        {/* Modal Header */}
        <div className="p-4 border-b border-parchment-outline-variant flex items-start justify-between gap-3 bg-parchment-container-low dark:bg-darkpaper-container">
          <div className="flex-1 min-w-0">
            <span className="text-[10px] font-mono tracking-label uppercase text-parchment-secondary block">
              Academic Paper Dossier
            </span>
            <h3 className="font-serif text-lg font-medium text-parchment-on-surface dark:text-darkpaper-on-surface truncate">
              {paper.title || paper.filename}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-parchment-secondary hover:text-parchment-primary"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-parchment-outline-variant text-xs font-serif bg-parchment-container-low/40">
          <button
            onClick={() => setActiveTab("metadata")}
            className={`px-4 py-2.5 font-medium border-b-2 transition-colors ${
              activeTab === "metadata"
                ? "border-parchment-primary text-parchment-primary bg-parchment-surface"
                : "border-transparent text-parchment-on-surface-variant hover:text-parchment-primary"
            }`}
          >
            Metadata & Abstract
          </button>
          <button
            onClick={() => setActiveTab("chunks")}
            className={`px-4 py-2.5 font-medium border-b-2 transition-colors ${
              activeTab === "chunks"
                ? "border-parchment-primary text-parchment-primary bg-parchment-surface"
                : "border-transparent text-parchment-on-surface-variant hover:text-parchment-primary"
            }`}
          >
            Extracted Chunks ({paper.total_chunks})
          </button>
          <button
            onClick={() => setActiveTab("graph")}
            className={`px-4 py-2.5 font-medium border-b-2 transition-colors ${
              activeTab === "graph"
                ? "border-parchment-primary text-parchment-primary bg-parchment-surface"
                : "border-transparent text-parchment-on-surface-variant hover:text-parchment-primary"
            }`}
          >
            Neo4j Knowledge Network
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 font-serif text-sm">
          {activeTab === "metadata" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 bg-parchment-container/40 border border-parchment-outline-variant text-xs">
                <div>
                  <span className="text-parchment-outline block text-[10px] font-mono uppercase">
                    Publication Year
                  </span>
                  <span className="font-medium text-parchment-on-surface">
                    {paper.publication_year || "Unknown"}
                  </span>
                </div>
                <div>
                  <span className="text-parchment-outline block text-[10px] font-mono uppercase">
                    Total Pages
                  </span>
                  <span className="font-medium text-parchment-on-surface">
                    {paper.total_pages} Pages
                  </span>
                </div>
                <div>
                  <span className="text-parchment-outline block text-[10px] font-mono uppercase">
                    Text Chunks
                  </span>
                  <span className="font-medium text-parchment-on-surface">
                    {paper.total_chunks} Segments
                  </span>
                </div>
                <div>
                  <span className="text-parchment-outline block text-[10px] font-mono uppercase">
                    Status
                  </span>
                  <Badge variant={paper.status === "indexed" ? "success" : "default"}>
                    {paper.status}
                  </Badge>
                </div>
              </div>

              {paper.authors && paper.authors.length > 0 && (
                <div>
                  <h5 className="text-xs font-mono tracking-label uppercase text-parchment-secondary mb-1">
                    Authors
                  </h5>
                  <div className="flex flex-wrap gap-1.5">
                    {paper.authors.map((author, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 bg-parchment-container text-xs border border-parchment-outline-variant"
                      >
                        {author}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <h5 className="text-xs font-mono tracking-label uppercase text-parchment-secondary mb-1">
                  Abstract
                </h5>
                <p className="p-3.5 bg-parchment-container-lowest dark:bg-darkpaper-container border border-parchment-outline-variant leading-relaxed text-parchment-on-surface">
                  {paper.abstract || "No abstract text extracted from this document."}
                </p>
              </div>

              {/* Action Banner */}
              <div className="pt-2 flex items-center justify-between border-t border-parchment-outline-variant">
                <span className="text-xs text-parchment-on-surface-variant font-mono">
                  File: {paper.filename}
                </span>

                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => extractMutation.mutate()}
                  disabled={extractMutation.isPending}
                >
                  {extractMutation.isPending ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5 mr-1" />
                  )}
                  <span>Extract Knowledge Graph (Neo4j)</span>
                </Button>
              </div>
            </div>
          )}

          {activeTab === "chunks" && (
            <div className="space-y-3">
              {paper.chunks?.map((chunk) => (
                <div
                  key={chunk.id}
                  className="p-3 border border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container text-xs"
                >
                  <div className="flex items-center justify-between mb-1.5 font-mono text-[10px] text-parchment-secondary">
                    <span>
                      Chunk #{chunk.chunk_index} • Page {chunk.page_number}
                    </span>
                    <span>Section: {chunk.section_name}</span>
                  </div>
                  <p className="leading-relaxed text-parchment-on-surface font-serif">
                    {chunk.text}
                  </p>
                </div>
              ))}
            </div>
          )}

          {activeTab === "graph" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-parchment-on-surface">
                    Extracted Knowledge Graph Subnetwork
                  </h4>
                  <p className="text-xs text-parchment-on-surface-variant">
                    {graphData?.total_nodes || 0} entities and {graphData?.total_edges || 0} relationships extracted.
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => extractMutation.mutate()}
                  disabled={extractMutation.isPending}
                >
                  <Sparkles className="w-3.5 h-3.5 mr-1" />
                  <span>Re-extract Graph</span>
                </Button>
              </div>

              {graphData && graphData.nodes.length > 0 ? (
                <div className="space-y-2">
                  <h5 className="text-[10px] font-mono tracking-label uppercase text-parchment-secondary">
                    Entities Extracted
                  </h5>
                  <div className="flex flex-wrap gap-1.5">
                    {graphData.nodes.map((node) => (
                      <span
                        key={node.id}
                        className="px-2 py-0.5 border border-parchment-outline-variant bg-parchment-container text-xs"
                      >
                        {node.name} <span className="opacity-50 text-[10px] uppercase">({node.type})</span>
                      </span>
                    ))}
                  </div>

                  <h5 className="text-[10px] font-mono tracking-label uppercase text-parchment-secondary mt-3">
                    Relationship Edges
                  </h5>
                  <div className="space-y-1.5 max-h-56 overflow-y-auto">
                    {graphData.edges.map((edge, idx) => (
                      <div
                        key={idx}
                        className="p-2 border border-parchment-outline-variant/60 bg-parchment-container/30 text-xs font-serif flex items-center gap-2"
                      >
                        <span className="font-medium text-parchment-primary">{edge.source}</span>
                        <span className="font-mono text-[10px] px-1 bg-amber-100 text-amber-900 border border-amber-300">
                          {edge.relation_type}
                        </span>
                        <span className="font-medium text-parchment-primary">{edge.target}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center p-6 border border-dashed border-parchment-outline-variant">
                  <Network className="w-8 h-8 text-parchment-outline mx-auto mb-2 opacity-50" />
                  <p className="text-xs text-parchment-on-surface-variant">
                    No graph triples currently built for this paper. Click "Extract Knowledge Graph" above to generate entities with LLM.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

