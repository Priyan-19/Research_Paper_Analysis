import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchPapers, deletePaper, embedPaperChunks } from "../api/papers";
import { PaperUploader } from "../components/papers/PaperUploader";
import { PaperDetailModal } from "../components/papers/PaperDetailModal";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { useUIStore } from "../store/useUIStore";
import { formatBytes, formatDate } from "../lib/utils";
import { Trash2, Sparkles, Eye, BookOpen, Layers, RefreshCw } from "lucide-react";
import { PaperListResponse, PaperResponse } from "../types/api";

export function PapersPage() {
  const queryClient = useQueryClient();
  const { showToast } = useUIStore();
  const [selectedPaperId, setSelectedPaperId] = useState<string | null>(null);

  // Live polling for paper list
  const { data, isLoading, refetch, isFetching } = useQuery<PaperListResponse>({
    queryKey: ["papers-list"],
    queryFn: () => fetchPapers(0, 100),
    refetchInterval: 10000,
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: (paperId: string) => deletePaper(paperId),
    onSuccess: () => {
      showToast("Paper, vector chunks, and Knowledge Graph triples deleted.", "info");
      queryClient.invalidateQueries({ queryKey: ["papers-list"] });
      queryClient.invalidateQueries({ queryKey: ["graph-stats"] });
    },
    onError: (err: any) => {
      showToast(`Delete failed: ${err.message}`, "error");
    },
  });

  // Re-embed Mutation
  const embedMutation = useMutation({
    mutationFn: (paperId: string) => embedPaperChunks(paperId),
    onSuccess: (res: any) => {
      showToast(`Regenerated vector embeddings for ${res.chunks_embedded} chunks.`, "success");
      queryClient.invalidateQueries({ queryKey: ["papers-list"] });
    },
    onError: (err: any) => {
      showToast(`Embedding failed: ${err.message}`, "error");
    },
  });

  const papers = data?.papers || [];

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-8 max-w-6xl mx-auto w-full space-y-8 font-serif">
      {/* Page Header */}
      <div className="border-b border-parchment-outline-variant pb-4 flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="text-[10px] font-mono tracking-label-wide uppercase text-parchment-secondary block">
            Corpus Management
          </span>
          <h1 className="text-2xl sm:text-3xl font-normal text-parchment-on-surface dark:text-darkpaper-on-surface">
            Research Papers & Ingestion Index
          </h1>
          <p className="text-sm text-parchment-on-surface-variant mt-1">
            Manage academic PDFs ingested into PostgreSQL pgvector dense vector store and Neo4j graph storage.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isFetching ? "animate-spin" : ""}`} />
            <span>Refresh Index</span>
          </Button>
        </div>
      </div>

      {/* Upload Component */}
      <section>
        <PaperUploader onUploadSuccess={() => queryClient.invalidateQueries({ queryKey: ["papers-list"] })} />
      </section>

      {/* Ingested Papers Table */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-parchment-secondary" />
            <h3 className="font-serif text-base font-medium text-parchment-on-surface dark:text-darkpaper-on-surface">
              Ingested Academic Repository ({papers.length} Papers)
            </h3>
          </div>
          <span className="text-xs font-mono text-parchment-secondary">
            Auto-polling every 10s
          </span>
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-sm text-parchment-secondary border border-parchment-outline-variant">
            Loading repository papers...
          </div>
        ) : papers.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container-low">
            <BookOpen className="w-10 h-10 text-parchment-outline mx-auto mb-2 opacity-50" />
            <p className="text-base text-parchment-on-surface">No research papers ingested yet.</p>
            <p className="text-xs text-parchment-on-surface-variant mt-1 font-mono">
              Upload PDF documents above to populate the semantic index and knowledge graph.
            </p>
          </div>
        ) : (
          <div className="border border-parchment-outline-variant overflow-x-auto bg-parchment-container-lowest dark:bg-darkpaper-container-low">
            <table className="w-full text-left text-xs font-serif divide-y divide-parchment-outline-variant">
              <thead>
                <tr className="bg-parchment-container-low dark:bg-darkpaper-container text-parchment-on-surface font-medium uppercase tracking-wider text-[10px] font-mono">
                  <th className="py-3 px-4">Title / Filename</th>
                  <th className="py-3 px-3">Authors</th>
                  <th className="py-3 px-3">Year</th>
                  <th className="py-3 px-3">Pages / Size</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Ingested</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-parchment-outline-variant/60">
                {papers.map((paper) => (
                  <tr
                    key={paper.id}
                    className="hover:bg-parchment-container/40 dark:hover:bg-darkpaper-container/40 transition-colors"
                  >
                    {/* Title */}
                    <td className="py-3.5 px-4 max-w-xs">
                      <div
                        onClick={() => setSelectedPaperId(paper.id)}
                        className="font-medium text-parchment-primary hover:underline cursor-pointer truncate"
                        title={paper.title || paper.filename}
                      >
                        {paper.title || paper.filename}
                      </div>
                      <div className="text-[10px] font-mono text-parchment-outline truncate">
                        {paper.filename}
                      </div>
                    </td>

                    {/* Authors */}
                    <td className="py-3.5 px-3 max-w-[140px] truncate text-parchment-on-surface-variant">
                      {paper.authors && paper.authors.length > 0
                        ? paper.authors.join(", ")
                        : "N/A"}
                    </td>

                    {/* Year */}
                    <td className="py-3.5 px-3 font-mono text-[11px] text-parchment-on-surface-variant">
                      {paper.publication_year || "—"}
                    </td>

                    {/* Pages & Size */}
                    <td className="py-3.5 px-3 font-mono text-[11px] text-parchment-on-surface-variant">
                      {paper.total_pages}p • {formatBytes(paper.file_size_bytes)}
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-3">
                      <Badge
                        variant={
                          paper.status === "indexed" || paper.status === "completed"
                            ? "success"
                            : paper.status === "failed"
                            ? "error"
                            : "default"
                        }
                      >
                        {paper.status}
                      </Badge>
                    </td>

                    {/* Ingested Date */}
                    <td className="py-3.5 px-3 font-mono text-[10px] text-parchment-outline">
                      {formatDate(paper.created_at)}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right space-x-1">
                      <button
                        onClick={() => setSelectedPaperId(paper.id)}
                        className="p-1 hover:text-parchment-primary border border-transparent hover:border-parchment-outline-variant transition-colors"
                        title="View Metadata & Dossier"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => embedMutation.mutate(paper.id)}
                        className="p-1 hover:text-parchment-primary border border-transparent hover:border-parchment-outline-variant transition-colors"
                        title="Recompute dense vector embeddings"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => {
                          if (confirm(`Delete paper "${paper.title || paper.filename}"? This will delete its vector embeddings from PostgreSQL and knowledge graph triples from Neo4j.`)) {
                            deleteMutation.mutate(paper.id);
                          }
                        }}
                        className="p-1 hover:text-rose-600 border border-transparent hover:border-rose-300 transition-colors"
                        title="Delete paper"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Detail Modal */}
      {selectedPaperId && (
        <PaperDetailModal
          paperId={selectedPaperId}
          onClose={() => setSelectedPaperId(null)}
        />
      )}
    </div>
  );
}
