import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import { ChatMessage } from "../../types/chat";
import { CitationChip } from "./CitationChip";
import { RetrievalDetails } from "./RetrievalDetails";
import { MessageActions } from "./MessageActions";
import { Copy, Check, Feather } from "lucide-react";
import { cn } from "../../lib/utils";

interface MessageBubbleProps {
  message: ChatMessage;
  onRegenerate?: () => void;
  onEditSubmit?: (newText: string) => void;
}

export function MessageBubble({ message, onRegenerate, onEditSubmit }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(message.content);

  const handleEditSubmit = () => {
    if (editText.trim() && onEditSubmit) {
      onEditSubmit(editText.trim());
      setIsEditing(false);
    }
  };

  // Pre-process citations in markdown text so citation chips render interactively
  const renderFormattedContent = (content: string) => {
    if (isUser) {
      return <p className="whitespace-pre-wrap font-serif text-[15px] leading-relaxed">{content}</p>;
    }

    return (
      <div className="prose prose-stone dark:prose-invert max-w-none font-serif text-[15px] leading-relaxed">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[[rehypeKatex, { throwOnError: false }], rehypeHighlight]}
          components={{
            // Custom Code Block with Copy Button
            code({ node, inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || "");
              const codeString = String(children).replace(/\n$/, "");

              if (!inline && match) {
                return (
                  <CodeBlock language={match[1]} code={codeString} />
                );
              }

              return (
                <code
                  className="px-1.5 py-0.5 text-xs font-mono bg-parchment-container dark:bg-darkpaper-container border border-parchment-outline-variant text-parchment-primary dark:text-darkpaper-primary"
                  {...props}
                >
                  {children}
                </code>
              );
            },
            // Custom Table styling for academic papers
            table({ children }) {
              return (
                <div className="overflow-x-auto my-4 border border-parchment-outline-variant">
                  <table className="min-w-full text-left text-xs font-serif divide-y divide-parchment-outline-variant">
                    {children}
                  </table>
                </div>
              );
            },
            th({ children }) {
              return (
                <th className="px-3 py-2 bg-parchment-container font-medium text-parchment-on-surface uppercase tracking-wider text-[11px]">
                  {children}
                </th>
              );
            },
            td({ children }) {
              return (
                <td className="px-3 py-2 text-parchment-on-surface-variant border-t border-parchment-outline-variant/50">
                  {children}
                </td>
              );
            },
            // Replace [1], [2], etc. inside paragraph text with CitationChip
            p({ children }) {
              return <p className="mb-3.5 last:mb-0">{renderChildrenWithCitations(children, message.citations)}</p>;
            },
          }}
        >
          {content}
        </ReactMarkdown>

        {message.isStreaming && (
          <span className="inline-block w-1.5 h-4 ml-1 bg-parchment-primary animate-pulse align-middle" />
        )}
      </div>
    );
  };

  return (
    <div
      className={cn(
        "group relative flex w-full gap-4 py-4 px-3 sm:px-6 transition-colors",
        isUser
          ? "justify-end bg-parchment-container-lowest/40 dark:bg-darkpaper-container/20"
          : "justify-start bg-transparent"
      )}
    >
      <div className={cn("flex max-w-3xl w-full gap-3.5", isUser ? "flex-row-reverse" : "flex-row")}>
        {/* Avatar */}
        <div className="flex-shrink-0 pt-0.5 select-none">
          {isUser ? (
            <div className="w-7 h-7 flex items-center justify-center border border-parchment-primary bg-parchment-primary text-parchment-on-primary text-xs font-mono">
              YOU
            </div>
          ) : (
            <div className="w-7 h-7 flex items-center justify-center border border-parchment-outline-variant bg-parchment-container text-parchment-secondary dark:bg-darkpaper-container dark:border-darkpaper-outline">
              <Feather className="w-3.5 h-3.5 text-parchment-primary dark:text-darkpaper-primary" />
            </div>
          )}
        </div>

        {/* Content Box */}
        <div className={cn("flex-1 min-w-0", isUser && "text-right")}>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono tracking-label uppercase text-parchment-secondary dark:text-darkpaper-outline">
              {isUser ? "Research Query" : "Assistant (Grounded RAG)"}
            </span>
            <span className="text-[10px] font-mono text-parchment-outline/70">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>

          {isEditing ? (
            <div className="space-y-2 mt-1">
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="w-full p-2.5 text-sm font-serif bg-parchment-container-lowest dark:bg-darkpaper-surface border border-parchment-outline text-parchment-on-surface outline-none"
                rows={3}
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-2.5 py-1 text-xs font-serif border border-parchment-outline"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEditSubmit}
                  className="px-3 py-1 text-xs font-serif bg-parchment-primary text-parchment-on-primary"
                >
                  Resubmit
                </button>
              </div>
            </div>
          ) : (
            renderFormattedContent(message.content)
          )}

          {/* Assistant Retrieval Collapsible Details */}
          {!isUser && !message.isStreaming && (
            <RetrievalDetails
              searchMode={message.search_mode}
              executionTime={message.metadata?.execution_time_seconds}
              provider={message.metadata?.llm_provider}
              totalCitations={message.citations?.length || message.metadata?.total_citations || 0}
              chunksCount={message.metadata?.chunks_count}
              graphHops={message.metadata?.graph_hops}
              insufficientEvidence={message.metadata?.insufficient_evidence}
            />
          )}

          {/* Action Row */}
          {!message.isStreaming && (
            <MessageActions
              content={message.content}
              role={message.role as "user" | "assistant"}
              onRegenerate={onRegenerate}
              onEdit={isUser ? () => setIsEditing(true) : undefined}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// Helper to replace inline citation tags [1], [Paper: ...], [Graph: ...] in markdown text with interactive CitationChip
function renderChildrenWithCitations(children: React.ReactNode, citations?: any[]): React.ReactNode {
  return React.Children.map(children, (child) => {
    if (typeof child === "string") {
      // Matches [1], [2], [Paper: ...], [Graph: ...]
      const parts = child.split(/(\[(?:Paper:[^\]]+|Graph:[^\]]+|\d+)\])/g);
      if (parts.length === 1) return child;

      return parts.map((part, idx) => {
        if (/^\[(?:Paper:[^\]]+|Graph:[^\]]+|\d+)\]$/.test(part)) {
          return <CitationChip key={idx} tag={part} allCitations={citations} />;
        }
        return part;
      });
    }
    return child;
  });
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-3 border border-parchment-outline-variant bg-[#1a1815] text-[#ede7dd] font-mono text-xs">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-[#38332c] bg-[#12110f] text-[10px] text-[#9e958a] uppercase tracking-wider">
        <span>{language}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-white transition-colors"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? "Copied" : "Copy"}</span>
        </button>
      </div>
      <div className="p-3 overflow-x-auto">
        <code>{code}</code>
      </div>
    </div>
  );
}

