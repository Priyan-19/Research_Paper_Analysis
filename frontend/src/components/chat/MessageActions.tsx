import React, { useState } from "react";
import { Copy, Check, RotateCcw, ThumbsUp, ThumbsDown, Edit3 } from "lucide-react";

interface MessageActionsProps {
  content: string;
  role: "user" | "assistant";
  onRegenerate?: () => void;
  onEdit?: () => void;
}

export function MessageActions({ content, role, onRegenerate, onEdit }: MessageActionsProps) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  return (
    <div className="flex items-center gap-1 mt-1 text-parchment-outline dark:text-darkpaper-outline opacity-0 group-hover:opacity-100 transition-opacity">
      <button
        onClick={handleCopy}
        className="p-1 hover:text-parchment-primary dark:hover:text-darkpaper-primary hover:bg-parchment-container transition-colors"
        title="Copy markdown text"
      >
        {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
      </button>

      {role === "user" && onEdit && (
        <button
          onClick={onEdit}
          className="p-1 hover:text-parchment-primary hover:bg-parchment-container transition-colors"
          title="Edit question & resubmit"
        >
          <Edit3 className="w-3.5 h-3.5" />
        </button>
      )}

      {role === "assistant" && (
        <>
          {onRegenerate && (
            <button
              onClick={onRegenerate}
              className="p-1 hover:text-parchment-primary hover:bg-parchment-container transition-colors"
              title="Regenerate grounded answer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={() => setFeedback(feedback === "up" ? null : "up")}
            className={`p-1 hover:text-parchment-primary transition-colors ${
              feedback === "up" ? "text-emerald-600" : ""
            }`}
            title="Helpful grounded answer"
          >
            <ThumbsUp className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setFeedback(feedback === "down" ? null : "down")}
            className={`p-1 hover:text-parchment-primary transition-colors ${
              feedback === "down" ? "text-rose-600" : ""
            }`}
            title="Report inaccurate or ungrounded claim"
          >
            <ThumbsDown className="w-3.5 h-3.5" />
          </button>
        </>
      )}
    </div>
  );
}

