import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { predictGnnLinks } from "../../api/graph";
import { Button } from "../ui/Button";
import { GNNLinkPredictionItem } from "../../types/api";
import { Brain, ArrowRight, Sparkles, Loader2 } from "lucide-react";
import { useUIStore } from "../../store/useUIStore";

export function LinkPredictionTab() {
  const { showToast } = useUIStore();
  const [sourceEntity, setSourceEntity] = useState("");
  const [candidatesText, setCandidatesText] = useState("");
  const [predictions, setPredictions] = useState<GNNLinkPredictionItem[]>([]);

  const predictMutation = useMutation({
    mutationFn: async () => {
      const candidates = candidatesText
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
      if (candidates.length === 0) {
        throw new Error("Please specify at least one candidate target entity.");
      }
      return predictGnnLinks(sourceEntity.trim(), candidates, 5);
    },
    onSuccess: (data) => {
      setPredictions(data.predicted_links);
      showToast(
        `GNN evaluated ${data.total_candidates_evaluated} prospective relationships.`,
        "success"
      );
    },
    onError: (err: any) => {
      showToast(err.message || "Failed to execute GNN link prediction", "error");
    },
  });

  return (
    <div className="space-y-4 p-4 font-serif">
      <div className="p-3 bg-purple-50 dark:bg-purple-950/20 border border-purple-200 text-xs text-purple-900 dark:text-purple-300 leading-relaxed">
        <div className="font-semibold flex items-center gap-1.5 mb-0.5">
          <Brain className="w-3.5 h-3.5 text-purple-700" />
          <span>Graph Neural Network (GNN) Link Prediction Engine</span>
        </div>
        Computes Graph Convolutional Network (GCN) embedding similarity in Neo4j relational space to discover unasserted research links, potential cross-disciplinary citations, and novel methodology pairings.
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Source Entity Input */}
        <div className="space-y-1">
          <label className="text-[11px] font-mono tracking-label uppercase text-parchment-secondary block">
            Source Research Entity
          </label>
          <input
            type="text"
            value={sourceEntity}
            onChange={(e) => setSourceEntity(e.target.value)}
            className="w-full p-2 text-xs font-serif bg-parchment-container-lowest dark:bg-darkpaper-container border border-parchment-outline-variant outline-none focus:border-parchment-primary"
            placeholder="e.g. BERT, Reciprocal Rank Fusion, LoRA"
          />
        </div>

        {/* Target Candidates */}
        <div className="space-y-1">
          <label className="text-[11px] font-mono tracking-label uppercase text-parchment-secondary block">
            Candidate Target Entities (one per line)
          </label>
          <textarea
            value={candidatesText}
            onChange={(e) => setCandidatesText(e.target.value)}
            rows={4}
            className="w-full p-2 text-xs font-serif bg-parchment-container-lowest dark:bg-darkpaper-container border border-parchment-outline-variant outline-none focus:border-parchment-primary leading-relaxed"
            placeholder="Entity candidates..."
          />
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={() => predictMutation.mutate()}
          disabled={predictMutation.isPending || !sourceEntity.trim()}
        >
          {predictMutation.isPending ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
          ) : (
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
          )}
          <span>Run GNN Inference</span>
        </Button>
      </div>

      {/* Predictions Output Table */}
      {predictions.length > 0 && (
        <div className="mt-4 border border-parchment-outline-variant bg-parchment-container-lowest dark:bg-darkpaper-container-low">
          <div className="p-3 border-b border-parchment-outline-variant bg-parchment-container-low font-mono text-[10px] uppercase text-parchment-secondary flex items-center justify-between">
            <span>Ranked Link Predictions for "{sourceEntity}"</span>
            <span>Probability & Cosine Metric</span>
          </div>

          <div className="divide-y divide-parchment-outline-variant">
            {predictions.map((p, idx) => (
              <div
                key={idx}
                className="p-3 flex items-center justify-between gap-3 text-xs hover:bg-parchment-container/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-medium text-parchment-secondary">
                    #{idx + 1}
                  </span>
                  <span className="font-medium text-parchment-primary">
                    {sourceEntity}
                  </span>
                  <ArrowRight className="w-3 h-3 text-parchment-outline" />
                  <span className="font-medium text-parchment-primary">
                    {p.target_entity}
                  </span>
                </div>

                <div className="flex items-center gap-3 font-mono text-[11px]">
                  <span className="text-emerald-700 font-medium">
                    {(p.link_probability * 100).toFixed(1)}% Prob
                  </span>
                  <span className="text-parchment-outline text-[10px]">
                    Sim: {p.similarity_score.toFixed(3)}
                  </span>
                  <span className="px-1.5 py-0.5 border text-[10px] uppercase bg-parchment-container border-parchment-outline-variant">
                    {p.gnn_recommendation}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

