import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, Square, BookOpen } from "lucide-react";
import { useChatStore } from "../../store/useChatStore";
import { SearchMode } from "../../types/api";
import { useQuery } from "@tanstack/react-query";
import { fetchPapers } from "../../api/papers";
import { cn } from "../../lib/utils";

interface ChatComposerProps {
  onSendMessage: (query: string) => void;
  isStreaming: boolean;
  onStopStreaming: () => void;
  isBackendOffline?: boolean;
}

export function ChatComposer({
  onSendMessage,
  isStreaming,
  onStopStreaming,
  isBackendOffline = false,
}: ChatComposerProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { searchMode, setSearchMode, paperScope, setPaperScope } = useChatStore();

  // Fetch papers for the Scope filter dropdown
  const { data: papersData } = useQuery({
    queryKey: ["papers-list-scope"],
    queryFn: () => fetchPapers(0, 100),
    staleTime: 30000,
  });

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 220)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (isStreaming) {
      onStopStreaming();
      return;
    }

    if (!input.trim() || isBackendOffline) return;
    onSendMessage(input.trim());
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4">
      <div className="relative bg-parchment-container-lowest dark:bg-darkpaper-container-low border border-parchment-outline-variant/80 focus-within:border-parchment-primary dark:focus-within:border-darkpaper-primary shadow-xs transition-colors">
        {/* Main Textarea Writing Area */}
        <div className="p-3.5 sm:p-4">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isBackendOffline}
            rows={2}
            placeholder={
              isBackendOffline
                ? "Backend API is currently offline. Please ensure FastAPI is running on port 8000."
                : "Ask a grounded research question across your papers... (Press Enter to send)"
            }
            className="w-full bg-transparent border-0 resize-none font-serif text-[15px] sm:text-[16px] text-parchment-on-surface dark:text-darkpaper-on-surface placeholder:text-parchment-secondary/50 focus:ring-0 outline-none leading-relaxed min-h-[46px] max-h-[220px]"
          />
        </div>

        {/* Bottom Toolbar: Mode pills + Paper Scope on Left, Char Count + Send Button on Right */}
        <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 border-t border-parchment-outline-variant/40 bg-parchment-container-low/40 dark:bg-darkpaper-container/30">
          <div className="flex items-center gap-2 flex-wrap">
            {/* Mode Selector */}
            <div className="inline-flex border border-parchment-outline-variant/60 bg-parchment-container-lowest dark:bg-darkpaper-container text-[11px] font-serif">
              {(["hybrid", "vector", "graph"] as SearchMode[]).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setSearchMode(mode)}
                  className={cn(
                    "px-2.5 py-1 capitalize transition-colors font-medium cursor-pointer",
                    searchMode === mode
                      ? "bg-parchment-primary text-parchment-on-primary dark:bg-darkpaper-primary dark:text-darkpaper-on-primary"
                      : "text-parchment-on-surface-variant hover:bg-parchment-container hover:text-parchment-primary dark:hover:bg-darkpaper-container-high"
                  )}
                >
                  {mode}
                </button>
              ))}
            </div>

            {/* Paper Scope Selector */}
            <div className="flex items-center gap-1.5 px-2 py-1 bg-parchment-container-lowest dark:bg-darkpaper-container border border-parchment-outline-variant/60 text-xs font-serif text-parchment-secondary">
              <BookOpen className="w-3 h-3 text-parchment-secondary flex-shrink-0" />
              <select
                value={paperScope || ""}
                onChange={(e) => setPaperScope(e.target.value || null)}
                className="bg-transparent border-0 outline-none cursor-pointer max-w-[150px] sm:max-w-[200px] truncate text-xs font-serif text-parchment-primary dark:text-darkpaper-primary"
              >
                <option value="">All Papers ({papersData?.total || 0})</option>
                {papersData?.papers?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title || p.filename}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Right: Char count + Send / Stop Button */}
          <div className="flex items-center gap-3">
            {input.length > 0 && (
              <span className="text-[10px] font-mono text-parchment-secondary/70 hidden sm:inline select-none">
                {input.length} chars
              </span>
            )}

            {isStreaming ? (
              <button
                type="button"
                onClick={onStopStreaming}
                className="w-8 h-8 flex items-center justify-center bg-rose-600 text-white hover:bg-rose-700 transition-colors cursor-pointer"
                title="Stop Generating (Esc)"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!input.trim() || isBackendOffline}
                className="w-8 h-8 flex items-center justify-center bg-parchment-primary text-parchment-on-primary hover:bg-parchment-primary-container disabled:opacity-20 disabled:cursor-not-allowed transition-all cursor-pointer dark:bg-darkpaper-primary dark:text-darkpaper-on-primary"
                title="Send Research Question (Enter)"
              >
                <ArrowUp className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
