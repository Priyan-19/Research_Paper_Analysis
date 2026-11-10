import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.graph.neo4j_builder import Neo4jGraphBuilder
from app.schemas.graph import KnowledgeGraphExtractionResult, GraphEntity, GraphRelationship, EntityType, RelationType


class AsyncIter:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        self.iter = iter(self.items)
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration


class TestNeo4jBuilder:
    """Unit tests for Neo4j Knowledge Graph construction and Cypher query execution."""

    @pytest.mark.asyncio
    async def test_persist_paper_graph(self, sample_graph_data):
        """Verifies session run calls for Paper node, Entity nodes, and relationships."""
        mock_session = AsyncMock()
        mock_session.run = AsyncMock()

        with patch("app.graph.neo4j_builder.get_neo4j_session") as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            success = await Neo4jGraphBuilder.persist_paper_graph(
                paper_id="paper_001",
                paper_title="Attention Is All You Need",
                graph_data=sample_graph_data
            )

            assert success is True
            assert mock_session.run.call_count == 1 + len(sample_graph_data.entities) + len(sample_graph_data.relationships)

    @pytest.mark.asyncio
    async def test_get_graph_stats(self):
        """Verifies parsing of database statistics into GraphStatsResponse."""
        mock_session = AsyncMock()

        async def _mock_run(query, **kwargs):
            if "MATCH (e:Entity)" in query:
                return AsyncIter([
                    {"type": "CONCEPT", "cnt": 6},
                    {"type": "METHOD", "cnt": 4}
                ])
            elif "MATCH ()-[r]->()" in query:
                return AsyncIter([
                    {"rel_type": "USES_METHOD", "cnt": 15},
                    {"rel_type": "EVALUATED_ON", "cnt": 10}
                ])
            return AsyncIter([])

        mock_session.run = _mock_run

        with patch("app.graph.neo4j_builder.get_neo4j_session") as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            stats = await Neo4jGraphBuilder.get_graph_stats()

            assert stats.total_nodes == 10
            assert stats.total_relationships == 25
            assert stats.entity_type_counts.get("CONCEPT") == 6
            assert stats.relationship_type_counts.get("USES_METHOD") == 15
