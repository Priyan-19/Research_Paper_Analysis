import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.embeddings.vector_store import VectorSearchResult
from app.analysis.citation_recommender import CitationRecommender
from app.schemas.analysis import (
    CitationRecommendRequest,
    CitationRecommendResponse,
    RecommendedCitationItem
)
from app.schemas.search import GraphSearchResponse, ConnectedPaperItem

client = TestClient(app)


def test_generate_heuristic_justification():
    """
    Tests recommendation justification generator formatting.
    """
    statement = "BERT uses bidirectional self-attention mechanisms."
    paper_title = "BERT Paper"
    snippet = "We introduce BERT..."

    justification = CitationRecommender._generate_heuristic_justification(
        statement=statement,
        paper_title=paper_title,
        snippet=snippet
    )

    assert "BERT Paper" in justification
    assert "BERT uses bidirectional" in justification


@pytest.mark.asyncio
async def test_recommend_citations_execution():
    """
    Tests CitationRecommender.recommend_citations calculation and sorting.
    """
    mock_db = MagicMock()

    with patch("app.embeddings.vector_store.VectorStoreService.search_vector_similarity", new_callable=AsyncMock) as mock_vsearch, \
         patch("app.rag.graph_retriever.GraphRetriever.search_graph", new_callable=AsyncMock) as mock_gsearch, \
         patch("app.services.paper_service.PaperService.get_paper_by_id", new_callable=AsyncMock) as mock_get_paper:

        mock_vsearch.return_value = [
            VectorSearchResult(
                chunk_id="c1",
                paper_id="paper_001",
                page_number=1,
                section_name="Abstract",
                text="BERT is a transformer model.",
                similarity_score=0.90
            ),
            VectorSearchResult(
                chunk_id="c2",
                paper_id="paper_002",
                page_number=2,
                section_name="Intro",
                text="GPT model overview.",
                similarity_score=0.60
            )
        ]
        mock_gsearch.return_value = GraphSearchResponse(
            query="BERT Transformer",
            matched_entities=["BERT"],
            total_triples=0,
            triples=[],
            connected_papers=[
                ConnectedPaperItem(
                    paper_id="paper_001",
                    paper_title="BERT Paper",
                    matched_entity_count=1
                )
            ],
            formatted_graph_context=""
        )

        mock_paper_model = MagicMock()
        mock_paper_model.title = "BERT: Pre-training of Deep Bidirectional Transformers"
        mock_get_paper.return_value = mock_paper_model

        statement = "Which papers describe BERT transformer architecture?"
        res = await CitationRecommender.recommend_citations(
            db=mock_db,
            statement=statement,
            top_k=5
        )

        assert res.statement == statement
        assert res.total_recommendations >= 1
        top_rec = res.recommendations[0]
        assert top_rec.paper_id == "paper_001"
        assert top_rec.vector_similarity == 0.90
        assert top_rec.overall_score > 0.5
        assert top_rec.justification != ""


def test_citation_recommend_api_endpoint():
    """
    Tests FastAPI REST endpoint POST /api/v1/citations/recommend.
    """
    payload = {
        "statement": "Transformers achieve state-of-the-art results on NLP tasks.",
        "top_k": 5
    }

    with patch.object(CitationRecommender, "recommend_citations", new_callable=AsyncMock) as mock_rec:
        mock_rec.return_value = CitationRecommendResponse(
            statement=payload["statement"],
            total_recommendations=1,
            recommendations=[
                RecommendedCitationItem(
                    paper_id="paper_001",
                    paper_title="Attention Is All You Need",
                    vector_similarity=0.95,
                    concept_overlap_score=1.0,
                    overall_score=0.97,
                    justification="Provides foundational attention mechanism results.",
                    relevant_snippet="We propose the Transformer..."
                )
            ]
        )

        res = client.post("/api/v1/citations/recommend", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["statement"] == payload["statement"]
        assert data["total_recommendations"] == 1
        assert data["recommendations"][0]["paper_id"] == "paper_001"
        assert data["recommendations"][0]["paper_title"] == "Attention Is All You Need"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
