import { useState } from "react";
import { ChevronDown, ChevronRight, Cpu, Layers, Network, Clock, ShieldCheck } from "lucide-react";
import { SearchMode } from "../../types/api";

interface RetrievalDetailsProps {
  searchMode?: SearchMode | string;
  executionTime?: number;
  provider?: string;
  totalCitations?: number;
  chunksCount?: number;
  graphHops?: number;
  insufficientEvidence?: boolean;
}

export function RetrievalDetails({
  searchMode = "hybrid",
  executionTime = 0,
  provider = "groq",
  totalCitations = 0,
  chunksCount = 5,
  graphHops = 2,
  insufficientEvidence = false,
}: RetrievalDetailsProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="mt-3 border-t border-parchment-outline-variant/60 pt-2 text-xs font-serif text-parchment-on-surface-variant">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-xs text-parchment-secondary hover:text-parchment-primary transition-colors cursor-pointer"
      >
        {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        <span className="font-mono tracking-label text-[11px] uppercase">
          Retrieval & Guardrail Details ({searchMode.toUpperCase()})
        </span>
      </button>

      {isOpen && (
        <div className="mt-2.5 p-3 bg-parchment-container/50 dark:bg-darkpaper-container/40 border border-parchment-outline-variant grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] font-mono">
          <div className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-parchment-secondary" />
            <div>
              <span className="text-parchment-outline block text-[9px] uppercase">Mode</span>
              <span className="font-medium text-parchment-on-surface capitalize">{searchMode} RAG</span>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-parchment-secondary" />
            <div>
              <span className="text-parchment-outline block text-[9px] uppercase">Model / Engine</span>
              <span className="font-medium text-parchment-on-surface uppercase">{provider}</span>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <Network className="w-3.5 h-3.5 text-parchment-secondary" />
            <div>
              <span className="text-parchment-outline block text-[9px] uppercase">Evidence Context</span>
              <span className="font-medium text-parchment-on-surface">
                {chunksCount} chunks • {graphHops} graph hops
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-parchment-secondary" />
            <div>
              <span className="text-parchment-outline block text-[9px] uppercase">Execution Latency</span>
              <span className="font-medium text-parchment-on-surface">
                {executionTime ? `${executionTime.toFixed(2)}s` : "< 1.5s"}
              </span>
            </div>
          </div>

          <div className="col-span-2 sm:col-span-4 pt-1.5 border-t border-parchment-outline-variant/50 flex items-center justify-between text-[10px]">
            <span className="flex items-center gap-1 text-emerald-700 dark:text-emerald-400">
              <ShieldCheck className="w-3 h-3" />
              <span>Grounded Citations Verified: {totalCitations}</span>
            </span>
            {insufficientEvidence && (
              <span className="text-amber-700 dark:text-amber-400 italic">
                ⚠️ Strict Guardrail Triggered: Insufficient evidence in corpus
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

