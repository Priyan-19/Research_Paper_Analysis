import pytest
from app.graph.extractor import GraphExtractor
from app.schemas.graph import KnowledgeGraphExtractionResult, EntityType


class TestEntityExtractor:
    """Unit tests for Knowledge Graph Extraction logic and heuristic fallback."""

    @pytest.mark.asyncio
    async def test_extract_graph_empty_text(self):
        """Returns empty extraction result on empty or whitespace text."""
        result = await GraphExtractor.extract_graph_from_text(
            text="   ",
            paper_id="paper_test",
            paper_title="Test Title"
        )
        assert isinstance(result, KnowledgeGraphExtractionResult)
        assert len(result.entities) == 0
        assert len(result.relationships) == 0

    def test_fallback_heuristic_extraction(self):
        """Domain-agnostic heuristic fallback correctly extracts capital terms and forms relationships."""
        text = (
            "We propose a Graph Neural Network (GNN) for academic paper link prediction. "
            "Our model integrates PyTorch, Neo4j, and Sentence Transformers on the Cora benchmark dataset."
        )
        title = "GNN Link Prediction in Academic Research"

        result = GraphExtractor._fallback_extraction(text=text, paper_title=title)

        assert isinstance(result, KnowledgeGraphExtractionResult)
        assert len(result.entities) > 0

        entity_names = [e.name.lower() for e in result.entities]
        # Should include paper title entity or extracted concepts
        assert any("gnn" in name or "pytorch" in name or "neo4j" in name or "academic" in name for name in entity_names)

        # Should form directed relationships connecting paper to extracted concepts
        assert len(result.relationships) > 0
        assert all(rel.source_entity != "" and rel.target_entity != "" for rel in result.relationships)

