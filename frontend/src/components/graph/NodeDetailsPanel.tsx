import { useNavigate } from "react-router-dom";
import { useChatStore } from "../../store/useChatStore";
import { X, MessageSquare, ExternalLink, Network } from "lucide-react";
import { Button } from "../ui/Button";

interface NodeDetailsPanelProps {
  node: {
    id: string;
    name: string;
    type: string;
    description?: string;
    neighbors?: string[];
  } | null;
  onClose: () => void;
}

export function NodeDetailsPanel({ node, onClose }: NodeDetailsPanelProps) {
  const navigate = useNavigate();
  const { createConversation, selectConversation, addUserMessage } = useChatStore();

  if (!node) return null;

  const handleAskAboutEntity = () => {
    const prompt = `What are the key findings, methodologies, and relationships involving '${node.name}' across the research papers?`;
    const newConvId = createConversation(prompt);
    addUserMessage(newConvId, prompt);
    selectConversation(newConvId);
    navigate("/chat");
  };

  return (
    <div className="absolute top-4 right-4 w-80 bg-parchment-container-lowest dark:bg-darkpaper-surface border border-parchment-outline-variant shadow-xl z-20 font-serif text-xs">
      {/* Header */}
      <div className="p-3 border-b border-parchment-outline-variant flex items-center justify-between bg-parchment-container-low dark:bg-darkpaper-container">
        <div>
          <span className="text-[10px] font-mono tracking-label uppercase text-parchment-secondary">
            Neo4j Node Entity
          </span>
          <h4 className="font-serif text-sm font-semibold text-parchment-primary truncate max-w-[220px]">
            {node.name}
          </h4>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-parchment-secondary hover:text-parchment-primary"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Body */}
      <div className="p-4 space-y-3">
        <div>
          <span className="text-[10px] font-mono uppercase text-parchment-outline block">
            Classification Type
          </span>
          <span className="inline-block mt-0.5 px-2 py-0.5 border border-parchment-outline-variant bg-parchment-container font-mono text-[11px] font-medium text-parchment-on-surface">
            {node.type}
          </span>
        </div>

        {node.description && (
          <div>
            <span className="text-[10px] font-mono uppercase text-parchment-outline block">
              Contextual Definition
            </span>
            <p className="mt-1 text-xs text-parchment-on-surface leading-relaxed">
              {node.description}
            </p>
          </div>
        )}

        {node.neighbors && node.neighbors.length > 0 && (
          <div>
            <span className="text-[10px] font-mono uppercase text-parchment-outline block mb-1">
              Connected Neighbor Entities ({node.neighbors.length})
            </span>
            <div className="flex flex-wrap gap-1 max-h-32 overflow-y-auto">
              {node.neighbors.map((n, idx) => (
                <span
                  key={idx}
                  className="px-1.5 py-0.5 text-[11px] bg-parchment-container/60 border border-parchment-outline-variant/60"
                >
                  {n}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="pt-2 border-t border-parchment-outline-variant">
          <Button
            variant="primary"
            className="w-full justify-center"
            onClick={handleAskAboutEntity}
          >
            <MessageSquare className="w-3.5 h-3.5 mr-1.5" />
            <span>Ask About This Entity</span>
          </Button>
        </div>
      </div>
    </div>
  );
}

