import { create } from "zustand";
import { persist } from "zustand/middleware";
import { Conversation, ChatMessage, RetrievedSource } from "../types/chat";
import { SearchMode, CitationBadge } from "../types/api";

interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  searchFilter: string;
  isStreaming: boolean;
  abortController: AbortController | null;
  paperScope: string | null; // null = all papers
  searchMode: SearchMode;

  // Actions
  setSearchFilter: (query: string) => void;
  setPaperScope: (paperId: string | null) => void;
  setSearchMode: (mode: SearchMode) => void;
  createConversation: (initialMessage?: string) => string;
  selectConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  renameConversation: (id: string, newTitle: string) => void;
  togglePinConversation: (id: string) => void;
  clearAllConversations: () => void;

  // Messaging actions
  addUserMessage: (conversationId: string, content: string) => string;
  addAssistantPlaceholder: (conversationId: string) => string;
  updateAssistantChunk: (
    conversationId: string,
    messageId: string,
    chunk: string,
    aggregated: string
  ) => void;
  finalizeAssistantMessage: (
    conversationId: string,
    messageId: string,
    answer: string,
    citations: CitationBadge[],
    sources: RetrievedSource[],
    metadata?: Record<string, any>
  ) => void;
  setStreamingState: (isStreaming: boolean, controller?: AbortController | null) => void;
  stopStreaming: () => void;
}

const DEFAULT_CONVERSATION_ID = "conv_default";

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      conversations: [
        {
          id: DEFAULT_CONVERSATION_ID,
          title: "New Research Inquiry",
          createdAt: Date.now(),
          updatedAt: Date.now(),
          isPinned: false,
          messages: [],
          paperScope: null,
        },
      ],
      activeConversationId: DEFAULT_CONVERSATION_ID,
      searchFilter: "",
      isStreaming: false,
      abortController: null,
      paperScope: null,
      searchMode: "hybrid",

      setSearchFilter: (query) => set({ searchFilter: query }),
      setPaperScope: (paperId) => set({ paperScope: paperId }),
      setSearchMode: (mode) => set({ searchMode: mode }),

      createConversation: (initialMessage?: string) => {
        const id = `conv_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
        const title = initialMessage
          ? initialMessage.slice(0, 36) + (initialMessage.length > 36 ? "..." : "")
          : "New Research Inquiry";

        const newConv: Conversation = {
          id,
          title,
          createdAt: Date.now(),
          updatedAt: Date.now(),
          isPinned: false,
          messages: [],
          paperScope: get().paperScope,
        };

        set((s) => ({
          conversations: [newConv, ...s.conversations],
          activeConversationId: id,
        }));
        return id;
      },

      selectConversation: (id) => {
        const conv = get().conversations.find((c) => c.id === id);
        if (conv) {
          set({
            activeConversationId: id,
            paperScope: conv.paperScope ?? null,
          });
        }
      },

      deleteConversation: (id) => {
        set((s) => {
          const filtered = s.conversations.filter((c) => c.id !== id);
          const nextActive =
            s.activeConversationId === id
              ? filtered[0]?.id || null
              : s.activeConversationId;
          return {
            conversations: filtered,
            activeConversationId: nextActive,
          };
        });
      },

      renameConversation: (id, newTitle) => {
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === id ? { ...c, title: newTitle, updatedAt: Date.now() } : c
          ),
        }));
      },

      togglePinConversation: (id) => {
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === id ? { ...c, isPinned: !c.isPinned, updatedAt: Date.now() } : c
          ),
        }));
      },

      clearAllConversations: () => {
        const newId = `conv_${Date.now()}`;
        set({
          conversations: [
            {
              id: newId,
              title: "New Research Inquiry",
              createdAt: Date.now(),
              updatedAt: Date.now(),
              isPinned: false,
              messages: [],
              paperScope: null,
            },
          ],
          activeConversationId: newId,
        });
      },

      addUserMessage: (conversationId, content) => {
        const msgId = `msg_${Date.now()}_u`;
        const userMsg: ChatMessage = {
          id: msgId,
          role: "user",
          content,
          timestamp: Date.now(),
          search_mode: get().searchMode,
        };

        set((s) => ({
          conversations: s.conversations.map((c) => {
            if (c.id !== conversationId) return c;
            // update title if it's the default title
            const shouldUpdateTitle =
              c.messages.length === 0 || c.title === "New Research Inquiry";
            const autoTitle = shouldUpdateTitle
              ? content.slice(0, 38) + (content.length > 38 ? "..." : "")
              : c.title;

            return {
              ...c,
              title: autoTitle,
              updatedAt: Date.now(),
              messages: [...c.messages, userMsg],
            };
          }),
        }));
        return msgId;
      },

      addAssistantPlaceholder: (conversationId) => {
        const msgId = `msg_${Date.now()}_a`;
        const placeholder: ChatMessage = {
          id: msgId,
          role: "assistant",
          content: "",
          timestamp: Date.now(),
          isStreaming: true,
          citations: [],
          retrieved_sources: [],
        };

        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === conversationId
              ? { ...c, messages: [...c.messages, placeholder], updatedAt: Date.now() }
              : c
          ),
        }));
        return msgId;
      },

      updateAssistantChunk: (conversationId, messageId, _chunk, aggregated) => {
        set((s) => ({
          conversations: s.conversations.map((c) => {
            if (c.id !== conversationId) return c;
            return {
              ...c,
              messages: c.messages.map((m) =>
                m.id === messageId ? { ...m, content: aggregated, isStreaming: true } : m
              ),
            };
          }),
        }));
      },

      finalizeAssistantMessage: (
        conversationId,
        messageId,
        answer,
        citations,
        sources,
        metadata
      ) => {
        set((s) => ({
          conversations: s.conversations.map((c) => {
            if (c.id !== conversationId) return c;
            return {
              ...c,
              updatedAt: Date.now(),
              messages: c.messages.map((m) =>
                m.id === messageId
                  ? {
                      ...m,
                      content: answer,
                      citations,
                      retrieved_sources: sources,
                      isStreaming: false,
                      metadata: metadata || m.metadata,
                    }
                  : m
              ),
            };
          }),
          isStreaming: false,
          abortController: null,
        }));
      },

      setStreamingState: (isStreaming, controller = null) => {
        set({ isStreaming, abortController: controller });
      },

      stopStreaming: () => {
        const { abortController } = get();
        if (abortController) {
          abortController.abort();
        }
        set({ isStreaming: false, abortController: null });
      },
    }),
    {
      name: "rag_chat_conversations",
      partialize: (state) => ({
        conversations: state.conversations,
        activeConversationId: state.activeConversationId,
        paperScope: state.paperScope,
        searchMode: state.searchMode,
      }),
    }
  )
);

