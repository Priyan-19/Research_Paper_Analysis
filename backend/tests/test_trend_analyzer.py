import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.graph import GraphStatsResponse
from app.analysis.trend_analyzer import TrendAnalyzer
from app.schemas.analysis import (
    TrendOverviewResponse,
    ConceptTimelineItem,
    ConceptCoOccurrenceItem,
    ResearchTrendsResponse
)

client = TestClient(app)


@pytest.mark.asyncio
async def test_get_trends_overview_execution():
    """
    Tests TrendAnalyzer.get_trends_overview structure.
    """
    mock_db = MagicMock()

    with patch("app.services.paper_service.PaperService.list_papers", new_callable=AsyncMock) as mock_list_papers, \
         patch("app.graph.neo4j_builder.Neo4jGraphBuilder.get_graph_stats", new_callable=AsyncMock) as mock_graph_stats, \
         patch("app.analysis.trend_analyzer.get_neo4j_session") as mock_neo4j_session:

        # Mock papers list
        p1 = MagicMock()
        p1.year = 2024
        p2 = MagicMock()
        p2.year = 2024
        mock_list_papers.return_value = [p1, p2]

        # Mock graph stats
        mock_graph_stats.return_value = GraphStatsResponse(
            total_nodes=15,
            total_relationships=25,
            entity_type_counts={"CONCEPT": 10},
            relationship_type_counts={"USES_METHOD": 5}
        )

        res = await TrendAnalyzer.get_trends_overview(db=mock_db)

        assert res.total_papers == 2
        assert res.total_concepts == 15
        assert res.total_relationships == 25
        assert res.publication_year_distribution.get("2024") == 2


def test_trends_overview_api_endpoint():
    """
    Tests FastAPI REST endpoint GET /api/v1/trends/overview.
    """
    with patch.object(TrendAnalyzer, "get_trends_overview", new_callable=AsyncMock) as mock_overview:
        mock_overview.return_value = TrendOverviewResponse(
            total_papers=5,
            total_concepts=20,
            total_relationships=35,
            top_concepts=[{"name": "BERT", "type": "MODEL", "paper_count": 4}],
            publication_year_distribution={"2024": 5}
        )

        res = client.get("/api/v1/trends/overview")
        assert res.status_code == 200
        data = res.json()
        assert data["total_papers"] == 5
        assert data["total_concepts"] == 20
        assert data["total_relationships"] == 35
        assert len(data["top_concepts"]) == 1
        assert data["top_concepts"][0]["name"] == "BERT"


def test_trends_timeline_api_endpoint():
    """
    Tests FastAPI REST endpoint GET /api/v1/trends/timeline.
    """
    with patch.object(TrendAnalyzer, "get_research_trends", new_callable=AsyncMock) as mock_trends:
        mock_trends.return_value = ResearchTrendsResponse(
            timeline=[
                ConceptTimelineItem(
                    concept_name="RAG",
                    entity_type="CONCEPT",
                    yearly_counts={"2023": 1, "2024": 3},
                    growth_rate=2.0,
                    is_emerging=True
                )
            ],
            emerging_concepts=["RAG"],
            top_co_occurrences=[
                ConceptCoOccurrenceItem(
                    concept1="RAG",
                    concept2="pgvector",
                    co_occurrence_count=3
                )
            ]
        )

        res = client.get("/api/v1/trends/timeline")
        assert res.status_code == 200
        data = res.json()
        assert len(data["timeline"]) == 1
        assert data["timeline"][0]["concept_name"] == "RAG"
        assert data["emerging_concepts"] == ["RAG"]
        assert len(data["top_co_occurrences"]) == 1
        assert data["top_co_occurrences"][0]["concept1"] == "RAG"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
