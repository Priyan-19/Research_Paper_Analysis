import { useRef, useEffect, useState } from "react";
import { useChatStore } from "../store/useChatStore";
import { useUIStore } from "../store/useUIStore";
import { useSettingsStore } from "../store/useSettingsStore";
import { MessageBubble } from "../components/chat/MessageBubble";
import { EmptyState } from "../components/chat/EmptyState";
import { ChatComposer } from "../components/chat/ChatComposer";
import { streamChat } from "../api/stream";
import { RetrievedSource } from "../types/chat";
import { ArrowDown } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "../api/health";

export function ChatPage() {
  const {
    conversations,
    activeConversationId,
    addUserMessage,
    addAssistantPlaceholder,
    updateAssistantChunk,
    finalizeAssistantMessage,
    isStreaming,
    setStreamingState,
    stopStreaming,
    searchMode,
    paperScope,
  } = useChatStore();

  const { openSourcesPanel, showToast } = useUIStore();
  const { topK, temperature } = useSettingsStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollBottom, setShowScrollBottom] = useState(false);
  const [userScrolledUp, setUserScrolledUp] = useState(false);

  // Health check to show offline warning
  const { isError: isHealthError } = useQuery({
    queryKey: ["backend-health"],
    queryFn: fetchHealth,
    refetchInterval: 15000,
  });

  const currentConversation = conversations.find(
    (c) => c.id === activeConversationId
  );
  const messages = currentConversation?.messages || [];

  // Handle user scroll detection
  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 80;
    setShowScrollBottom(!isAtBottom);
    setUserScrolledUp(!isAtBottom);
  };

  const scrollToBottom = (smooth = true) => {
    messagesEndRef.current?.scrollIntoView({
      behavior: smooth ? "smooth" : "auto",
    });
    setUserScrolledUp(false);
  };

  useEffect(() => {
    if (!userScrolledUp) {
      scrollToBottom();
    }
  }, [messages, userScrolledUp]);

  // Main Send Message Handler
  const handleSendMessage = (queryText: string) => {
    if (!activeConversationId) return;

    // 1. Add user message
    addUserMessage(activeConversationId, queryText);

    // 2. Add assistant placeholder
    const assistantMsgId = addAssistantPlaceholder(activeConversationId);
    setStreamingState(true);

    // 3. Initiate Stream
    const controller = streamChat({
      request: {
        query: queryText,
        search_mode: searchMode,
        paper_id: paperScope || null,
        top_k: topK,
        temperature: temperature,
      },
      onChunk: (_chunk, aggregated) => {
        updateAssistantChunk(activeConversationId, assistantMsgId, _chunk, aggregated);
      },
      onComplete: (data) => {
        // Construct retrieved sources for Sources panel
        const sources: RetrievedSource[] = (data.citations || []).map((c: any, i) => ({
          source_index: i + 1,
          source_type: c.source_type || (data.search_mode === "graph" ? "graph" : data.search_mode === "hybrid" ? "hybrid" : "vector"),
          paper_id: c.paper_id,
          paper_title: c.paper_title,
          page_number: c.page_number,
          section_name: c.section_name,
          snippet: c.snippet || "Retrieved evidence passage referenced in response.",
          relationship: c.relationship,
          source_entity: c.source_entity,
          target_entity: c.target_entity,
          score: c.score,
        }));

        finalizeAssistantMessage(
          activeConversationId,
          assistantMsgId,
          data.answer,
          data.citations || [],
          sources,
          {
            llm_provider: data.llm_provider,
            execution_time_seconds: data.execution_time_seconds,
            total_citations: data.total_citations,
            insufficient_evidence: data.insufficient_evidence,
            chunks_count: topK,
            graph_hops: 2,
          }
        );

        // Preload sources panel data
        openSourcesPanel(sources, null, data.search_mode === "graph" ? "graph" : "papers");
      },
      onError: (err) => {
        showToast(err.message || "Failed to generate answer", "error");
        finalizeAssistantMessage(
          activeConversationId,
          assistantMsgId,
          `⚠️ **Error encountered during retrieval or generation:**\n\n${err.message}\n\nPlease check backend logs and confirm database connectivity.`,
          [],
          []
        );
      },
    });

    setStreamingState(true, controller);
  };

  const handleRegenerate = () => {
    if (messages.length < 2) return;
    const lastUserMessage = [...messages].reverse().find((m) => m.role === "user");
    if (lastUserMessage) {
      handleSendMessage(lastUserMessage.content);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full relative">
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center p-4 sm:p-6 w-full max-w-3xl mx-auto my-auto">
          <EmptyState />
          <div className="w-full">
            <ChatComposer
              onSendMessage={handleSendMessage}
              isStreaming={isStreaming}
              onStopStreaming={stopStreaming}
              isBackendOffline={isHealthError}
            />
          </div>
        </div>
      ) : (
        <>
          {/* Messages Scroll Area */}
          <div
            ref={scrollContainerRef}
            onScroll={handleScroll}
            className="flex-1 overflow-y-auto overflow-x-hidden flex flex-col"
          >
            <div className="flex-1 py-4 divide-y divide-parchment-outline-variant/30">
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  onRegenerate={msg.role === "assistant" ? handleRegenerate : undefined}
                  onEditSubmit={msg.role === "user" ? handleSendMessage : undefined}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Floating Scroll to Bottom Button */}
          {showScrollBottom && (
            <button
              onClick={() => scrollToBottom()}
              className="absolute bottom-24 right-8 p-2 bg-parchment-container border border-parchment-outline text-parchment-primary hover:bg-parchment-container-high transition-all shadow-md z-10"
              title="Scroll to bottom"
            >
              <ArrowDown className="w-4 h-4" />
            </button>
          )}

          {/* Sticky Bottom Composer */}
          <ChatComposer
            onSendMessage={handleSendMessage}
            isStreaming={isStreaming}
            onStopStreaming={stopStreaming}
            isBackendOffline={isHealthError}
          />
        </>
      )}
    </div>
  );
}
