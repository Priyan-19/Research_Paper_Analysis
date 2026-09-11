import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.rag.citation_guard import CitationGuard
from app.rag.chat_service import GroundedChatService
from app.schemas.rag import (
    ChatRequest,
    ChatResponse,
    CitationBadge,
    SearchModeEnum
)
from app.schemas.search import HybridSearchResponse, HybridSearchResultItem

client = TestClient(app)


def test_citation_guard_badge_extraction():
    """
    Tests CitationGuard regex extraction of inline citation tags from LLM text.
    """
    answer_text = (
        "BERT uses bidirectional transformer representations [Paper: paper_001, Page: 4]. "
        "It achieves high accuracy on GLUE [Source 1]."
    )
    retrieved_sources = [
        {
            "source_index": 1,
            "paper_id": "paper_001",
            "paper_title": "BERT Paper",
            "page_number": 4,
            "section_name": "Methodology",
            "text": "BERT model overview"
        }
    ]

    badges = CitationGuard.extract_citation_badges(answer_text, retrieved_sources)

    assert len(badges) >= 1
    assert any(b.paper_id == "paper_001" for b in badges)
    assert any(b.page_number == 4 for b in badges)


def test_insufficient_evidence_guardrail():
    """
    Tests CitationGuard insufficient evidence detection and fallback message.
    """
    assert CitationGuard.is_insufficient_evidence("", []) is True

    answer_declaring_lacking_evidence = "Based on the available research papers, there is insufficient evidence to answer this question."
    assert CitationGuard.is_insufficient_evidence(answer_declaring_lacking_evidence, [{"text": "sample"}]) is True

    msg = CitationGuard.get_insufficient_evidence_message("What is Quantum Computing?")
    assert "insufficient evidence" in msg
    assert "Quantum Computing" in msg


@pytest.mark.asyncio
async def test_grounded_chat_service_hybrid_mode():
    """
    Tests GroundedChatService end-to-end execution flow with mocked retrieval and LLM.
    """
    mock_db = MagicMock()

    with patch("app.rag.hybrid_retriever.HybridRetriever.search_hybrid", new_callable=AsyncMock) as mock_hybrid, \
         patch("app.rag.chat_service.get_llm_provider") as mock_get_llm:

        mock_hybrid.return_value = HybridSearchResponse(
            query="Tell me about BERT",
            total_results=1,
            results=[
                HybridSearchResultItem(
                    item_id="chunk_c1",
                    item_type="vector_chunk",
                    content="BERT is a language representation model.",
                    paper_id="paper_001",
                    vector_rank=1,
                    rrf_score=0.016,
                    metadata={"page_number": 2, "section_name": "Introduction"}
                )
            ],
            matched_graph_entities=["BERT"],
            unified_hybrid_context="BERT context"
        )

        mock_llm = MagicMock()
        mock_llm.provider_name = "gemini"
        mock_llm.generate_text = AsyncMock(return_value="BERT is introduced in [Paper: paper_001, Page: 2].")
        mock_llm.generate = AsyncMock(return_value="BERT is introduced in [Paper: paper_001, Page: 2].")
        mock_get_llm.return_value = mock_llm

        request = ChatRequest(query="Tell me about BERT", search_mode=SearchModeEnum.HYBRID)
        response = await GroundedChatService.generate_grounded_chat(db=mock_db, request=request)

        assert response.query == "Tell me about BERT"
        assert response.search_mode == "hybrid"
        assert response.insufficient_evidence is False
        assert response.total_citations >= 1
        assert response.citations[0].paper_id == "paper_001"


def test_chat_api_endpoint():
    """
    Tests FastAPI REST endpoint POST /api/v1/chat.
    """
    payload = {
        "query": "What is BERT?",
        "search_mode": "hybrid",
        "top_k": 5
    }

    with patch.object(GroundedChatService, "generate_grounded_chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = ChatResponse(
            query=payload["query"],
            answer="BERT is a transformer model [Paper: paper_001].",
            search_mode="hybrid",
            total_citations=1,
            citations=[
                CitationBadge(
                    paper_id="paper_001",
                    paper_title="BERT Paper",
                    page_number=1,
                    section_name="Intro",
                    citation_tag="[Paper: paper_001]",
                    snippet="BERT overview"
                )
            ],
            insufficient_evidence=False,
            llm_provider="gemini",
            execution_time_seconds=0.15
        )

        res = client.post("/api/v1/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == payload["query"]
        assert data["search_mode"] == "hybrid"
        assert data["total_citations"] == 1
        assert data["citations"][0]["paper_id"] == "paper_001"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
