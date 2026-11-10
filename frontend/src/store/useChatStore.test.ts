import { describe, it, expect } from "vitest";
import { useChatStore } from "./useChatStore";

describe("useChatStore", () => {
  it("creates a new conversation and sets it active", () => {
    const newId = useChatStore.getState().createConversation("What is Hybrid RAG?");
    expect(newId).toBeDefined();

    const state = useChatStore.getState();
    expect(state.activeConversationId).toBe(newId);
    const conv = state.conversations.find((c) => c.id === newId);
    expect(conv).toBeDefined();
    expect(conv?.title).toBe("What is Hybrid RAG?");
  });

  it("updates search mode and paper scope", () => {
    useChatStore.getState().setSearchMode("graph");
    expect(useChatStore.getState().searchMode).toBe("graph");

    useChatStore.getState().setPaperScope("paper_123");
    expect(useChatStore.getState().paperScope).toBe("paper_123");

    useChatStore.getState().setPaperScope(null);
    expect(useChatStore.getState().paperScope).toBeNull();
  });

  it("adds user messages and assistant placeholders", () => {
    const convId = useChatStore.getState().createConversation("Test Conversation");
    const userMsgId = useChatStore.getState().addUserMessage(convId, "Explain BERT architecture.");
    expect(userMsgId).toBeDefined();

    const asstMsgId = useChatStore.getState().addAssistantPlaceholder(convId);
    expect(asstMsgId).toBeDefined();

    const conv = useChatStore.getState().conversations.find((c) => c.id === convId);
    expect(conv?.messages).toHaveLength(2);
    expect(conv?.messages[0].role).toBe("user");
    expect(conv?.messages[0].content).toBe("Explain BERT architecture.");
    expect(conv?.messages[1].role).toBe("assistant");
    expect(conv?.messages[1].isStreaming).toBe(true);
  });

  it("finalizes assistant message with citations and evidence", () => {
    const convId = useChatStore.getState().createConversation("Finalize Test");
    useChatStore.getState().addUserMessage(convId, "Question?");
    const asstMsgId = useChatStore.getState().addAssistantPlaceholder(convId);

    const mockCitations = [
      {
        paper_id: "p1",
        paper_title: "Attention",
        page_number: 1,
        citation_tag: "[Paper: p1, Page: 1]",
      },
    ];

    useChatStore.getState().finalizeAssistantMessage(
      convId,
      asstMsgId,
      "Final grounded answer [Paper: p1, Page: 1].",
      mockCitations,
      []
    );

    const conv = useChatStore.getState().conversations.find((c) => c.id === convId);
    const finalized = conv?.messages.find((m) => m.id === asstMsgId);
    expect(finalized?.isStreaming).toBe(false);
    expect(finalized?.content).toBe("Final grounded answer [Paper: p1, Page: 1].");
    expect(finalized?.citations).toHaveLength(1);
  });

  it("renames and deletes conversations", () => {
    const convId = useChatStore.getState().createConversation("Original Name");
    useChatStore.getState().renameConversation(convId, "Renamed Inquiry");

    let conv = useChatStore.getState().conversations.find((c) => c.id === convId);
    expect(conv?.title).toBe("Renamed Inquiry");

    useChatStore.getState().deleteConversation(convId);
    conv = useChatStore.getState().conversations.find((c) => c.id === convId);
    expect(conv).toBeUndefined();
  });
});

