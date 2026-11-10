import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.embeddings.vector_store import VectorStoreService, VectorSearchResult
from app.core.exceptions import ResourceNotFoundError


class TestVectorStore:
    """Unit tests for VectorStoreService embedding persistence and similarity query logic."""

    @pytest.mark.asyncio
    async def test_search_vector_similarity_empty_query(self, mock_async_db_session):
        """Empty or whitespace query string immediately returns empty list."""
        results = await VectorStoreService.search_vector_similarity(
            db=mock_async_db_session,
            query_text="   "
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_search_vector_similarity_with_mock_results(self, mock_async_db_session):
        """Parses rows into VectorSearchResult objects and applies threshold filtering."""
        mock_chunk = MagicMock()
        mock_chunk.id = "chunk_001"
        mock_chunk.paper_id = "paper_001"
        mock_chunk.page_number = 1
        mock_chunk.section_name = "Introduction"
        mock_chunk.text = "BERT uses bidirectional self-attention."

        mock_rows = [
            (mock_chunk, 0.85, "BERT Paper", "bert.pdf"),
            (mock_chunk, 0.10, "Irrelevant Paper", "other.pdf"),  # Below 0.20 threshold
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_async_db_session.execute.return_value = mock_result

        with patch("app.embeddings.vector_store.get_embedding_service") as mock_get_embed:
            mock_embed = MagicMock()
            mock_embed.embed_text.return_value = [0.1] * 384
            mock_get_embed.return_value = mock_embed

            results = await VectorStoreService.search_vector_similarity(
                db=mock_async_db_session,
                query_text="Tell me about BERT",
                top_k=5,
                min_similarity_threshold=0.20
            )

            assert len(results) == 1
            assert results[0].chunk_id == "chunk_001"
            assert results[0].paper_id == "paper_001"
            assert results[0].similarity_score == 0.85
            assert results[0].paper_title == "BERT Paper"

    @pytest.mark.asyncio
    async def test_embed_paper_chunks_non_existent_paper(self, mock_async_db_session):
        """Raises ResourceNotFoundError when paper_id does not exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_async_db_session.execute.return_value = mock_result

        with pytest.raises(ResourceNotFoundError):
            await VectorStoreService.embed_paper_chunks(
                db=mock_async_db_session,
                paper_id="non_existent_paper"
            )

