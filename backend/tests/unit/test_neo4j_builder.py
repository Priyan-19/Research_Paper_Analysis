import pytest
from contextlib import asynccontextmanager
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


@asynccontextmanager
async def _mock_neo4j_ctx(session):
    yield session


class TestNeo4jBuilder:
    """Unit tests for Neo4j Knowledge Graph construction and Cypher query execution."""

    @pytest.mark.asyncio
    async def test_persist_paper_graph(self, sample_graph_data):
        """Verifies session run calls for Paper node, Entity nodes, and relationships."""
        mock_session = AsyncMock()
        mock_session.run = AsyncMock()

        with patch("app.graph.neo4j_builder.get_neo4j_session", side_effect=lambda: _mock_neo4j_ctx(mock_session)):
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

        with patch("app.graph.neo4j_builder.get_neo4j_session", side_effect=lambda: _mock_neo4j_ctx(mock_session)):
            stats = await Neo4jGraphBuilder.get_graph_stats()

            assert stats.total_nodes == 10
            assert stats.total_relationships == 25
            assert stats.entity_type_counts.get("CONCEPT") == 6
            assert stats.relationship_type_counts.get("USES_METHOD") == 15

    @pytest.mark.asyncio
    async def test_paper_service_delete_paper_cleans_neo4j(self):
        """Verifies that PaperService.delete_paper issues Neo4j Cypher queries for edges, paper node, and orphans."""
        from app.services.paper_service import PaperService
        from app.models.paper import Paper

        mock_paper = Paper(
            id="p_999",
            title="Heart Disease Paper",
            filename="heart.pdf",
            file_path="nonexistent_heart.pdf",
            file_size_bytes=1000,
            total_pages=5
        )

        mock_db = AsyncMock()
        mock_session = AsyncMock()
        executed_queries = []

        async def _mock_run(query, **kwargs):
            executed_queries.append((query, kwargs))
            return AsyncIter([])

        mock_session.run = _mock_run

        with patch.object(PaperService, "get_paper_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_paper
            with patch("app.database.neo4j.get_neo4j_session", side_effect=lambda: _mock_neo4j_ctx(mock_session)):

                result = await PaperService.delete_paper(mock_db, "p_999")

                assert result is True
                # Assert Neo4j session was called with 3 clean-up queries
                assert len(executed_queries) == 3
                assert "WHERE r.paper_id = $paper_id DELETE r" in executed_queries[0][0]
                assert "MATCH (p:Paper {id: $paper_id}) DETACH DELETE p" in executed_queries[1][0]
                assert "MATCH (e:Entity) WHERE NOT (e)--() DETACH DELETE e" in executed_queries[2][0]
                # Assert Postgres DB delete and commit
                mock_db.delete.assert_awaited_once_with(mock_paper)
                mock_db.commit.assert_awaited_once()
