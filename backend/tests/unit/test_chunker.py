import pytest
from app.ingestion.chunker import SemanticChunker, ChunkData
from app.ingestion.pdf_loader import PageContent


class TestSemanticChunker:
    """Unit tests for recursive semantic chunking and metadata preservation."""

    def test_chunking_retains_page_and_section_metadata(self):
        """Validates that extracted chunks carry the correct page and section names."""
        pages = [
            PageContent(
                page_number=1,
                text="1. Introduction\n\n" + ("Deep learning has revolutionized artificial intelligence. " * 30)
            ),
            PageContent(
                page_number=2,
                text="3. Methodology\n\n" + ("We propose a novel Transformer based model for multi-hop graph QA. " * 30)
            )
        ]

        chunker = SemanticChunker(target_chunk_size=400, chunk_overlap=50)
        chunks = chunker.chunk_pages(pages)

        assert len(chunks) >= 2
        assert chunks[0].page_number == 1
        assert chunks[0].section_name == "Introduction"
        assert chunks[-1].page_number == 2
        assert chunks[-1].section_name == "Methodology"

    def test_chunking_empty_pages(self):
        """Chunking empty page list returns empty list."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_pages([])
        assert chunks == []

    def test_chunking_short_page(self):
        """Handles pages with text shorter than target chunk size."""
        pages = [PageContent(page_number=1, text="Brief abstract summarizing our key findings in NLP.")]
        chunker = SemanticChunker(target_chunk_size=700, chunk_overlap=100)
        chunks = chunker.chunk_pages(pages)
        assert len(chunks) == 1
        assert "Brief abstract" in chunks[0].text
        assert chunks[0].page_number == 1

    def test_chunk_attributes(self):
        """Verifies ChunkData attributes and sizing limits."""
        chunker = SemanticChunker(target_chunk_size=300, chunk_overlap=50)
        pages = [PageContent(page_number=1, text=("Natural Language Processing models have grown exponentially. " * 20))]
        chunks = chunker.chunk_pages(pages)

        for c in chunks:
            assert isinstance(c, ChunkData)
            assert c.char_length > 0
            assert c.token_count > 0
            assert c.chunk_index >= 0
            assert c.text.strip() != ""
