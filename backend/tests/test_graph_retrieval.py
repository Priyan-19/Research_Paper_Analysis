import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.rag.graph_retriever import QueryEntityExtractor, GraphRetriever
from app.schemas.search import (
    GraphSearchRequest,
    GraphSearchResponse,
    GraphTripleItem,
    ConnectedPaperItem
)

client = TestClient(app)


@pytest.mark.asyncio
async def test_query_entity_extractor_heuristics():
    """
    Tests rule-based heuristic entity extraction from natural language question.
    """
    query = "Which models were evaluated on the GLUE benchmark using BERT and Sentence Transformers?"
    entities = await QueryEntityExtractor.extract_query_entities(query)
    
    assert "GLUE" in entities
    assert "BERT" in entities
    assert "Sentence Transformers" in entities or "Sentence-Transformers" in entities


def test_build_formatted_graph_context():
    """
    Tests text context formatting for LLM prompt augmentation.
    """
    triples = [
        GraphTripleItem(
            source="BERT",
            relation_type="EVALUATED_ON",
            target="GLUE",
            description="Tested on GLUE benchmark tasks",
            paper_id="paper_001"
        )
    ]
    connected_papers = [
        ConnectedPaperItem(
            paper_id="paper_001",
            paper_title="BERT: Pre-training of Deep Bidirectional Transformers",
            matched_entity_count=2
        )
    ]

    context = GraphRetriever.build_formatted_graph_context(triples, connected_papers)

    assert "=== KNOWLEDGE GRAPH EVIDENCE & ENTITY RELATIONS ===" in context
    assert "BERT" in context
    assert "EVALUATED_ON" in context
    assert "GLUE" in context
    assert "paper_001" in context


@pytest.mark.asyncio
async def test_search_graph_empty_query():
    """
    Tests search_graph behavior when query contains no extractable entities.
    """
    response = await GraphRetriever.search_graph(query="   ")
    assert response.matched_entities == []
    assert response.total_triples == 0
    assert response.triples == []


def test_search_graph_api_endpoint():
    """
    Tests FastAPI POST /api/v1/search/graph endpoint payload handling.
    """
    payload = {
        "query": "What is BERT model evaluated on GLUE dataset?",
        "top_k": 5,
        "max_depth": 2
    }

    with patch.object(GraphRetriever, "search_graph", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = GraphSearchResponse(
            query=payload["query"],
            matched_entities=["BERT", "GLUE"],
            total_triples=1,
            triples=[
                GraphTripleItem(
                    source="BERT",
                    relation_type="EVALUATED_ON",
                    target="GLUE",
                    description="Evaluated on GLUE",
                    paper_id="paper_001"
                )
            ],
            connected_papers=[
                ConnectedPaperItem(
                    paper_id="paper_001",
                    paper_title="BERT Paper",
                    matched_entity_count=2
                )
            ],
            formatted_graph_context="Formatted Context"
        )

        res = client.post("/api/v1/search/graph", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["query"] == payload["query"]
        assert data["matched_entities"] == ["BERT", "GLUE"]
        assert data["total_triples"] == 1
        assert len(data["triples"]) == 1
        assert data["triples"][0]["source"] == "BERT"
        assert data["triples"][0]["relation_type"] == "EVALUATED_ON"
        assert data["triples"][0]["target"] == "GLUE"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
