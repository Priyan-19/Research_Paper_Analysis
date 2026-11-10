import pytest
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock

from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import SemanticChunker
from app.embeddings.sentence_transformer import SentenceTransformerEmbedding
from app.graph.extractor import GraphExtractor
from app.graph.canonicalizer import EntityCanonicalizer
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.citation_guard import CitationGuard
from app.embeddings.vector_store import VectorSearchResult
from app.schemas.search import GraphTripleItem
from app.workers.paper_processing import PaperProcessingWorker


class TestPipelineIntegration:
    """
    Integration tests verifying multi-component interaction across the pipeline:
    1. Ingestion: PDF -> Parser -> Chunker
    2. Embeddings: Chunks -> SentenceTransformer vector generation
    3. Graph: Entity Extraction -> Canonicalization
    4. Hybrid RAG: Vector + Graph -> Reciprocal Rank Fusion -> Citation Guard
    5. Background Worker: End-to-end processing pipeline
    """

    def test_pdf_to_chunker_pipeline(self, sample_pdf_path):
        """Integration: PDF file extraction cleanly feeds into SemanticChunker preserving pages."""
        pages = PDFLoader.extract_pages(sample_pdf_path)
        assert len(pages) == 2

        chunker = SemanticChunker(target_chunk_size=300, chunk_overlap=50)
        chunks = chunker.chunk_pages(pages)

        assert len(chunks) >= 2
        assert chunks[0].page_number == 1
        assert chunks[-1].page_number == 2
        assert all(len(c.text) > 0 for c in chunks)

    def test_chunker_to_embeddings_pipeline(self, sample_pdf_path):
        """Integration: Extracted chunks feed into SentenceTransformers generating 384-d vectors."""
        pages = PDFLoader.extract_pages(sample_pdf_path)
        chunker = SemanticChunker(target_chunk_size=300, chunk_overlap=50)
        chunks = chunker.chunk_pages(pages)

        embedder = SentenceTransformerEmbedding()
        # Mock underlying neural weights returning a numpy 2D array
        mock_model = MagicMock()
        mock_model.encode.side_effect = lambda texts, **kw: np.full((len(texts), 384), 0.05)
        embedder._model = mock_model

        chunk_texts = [c.text for c in chunks]
        vectors = embedder.embed_batch(chunk_texts)

        assert len(vectors) == len(chunks)
        assert all(len(v) == 384 for v in vectors)

    def test_extraction_to_canonicalization_pipeline(self):
        """Integration: Heuristic extraction directly flows into EntityCanonicalizer deduplication."""
        text = (
            "Large Language Models (LLMs) and Retrieval Augmented Generation (RAG) "
            "are benchmarked on the GLUE dataset using BERT models."
        )
        title = "Modern NLP Architectures"

        raw_graph = GraphExtractor._fallback_extraction(text=text, paper_title=title)
        canonical_graph = EntityCanonicalizer.canonicalize_graph(raw_graph)

        assert len(canonical_graph.entities) > 0
        names = {e.name for e in canonical_graph.entities}
        assert any(n in names for n in ["RAG", "LLM", "BERT", "Modern Nlp Architectures"])

    def test_hybrid_retrieval_to_citation_guard_pipeline(self):
        """Integration: RRF fusion results feed into CitationGuard badge extraction."""
        vector_res = [
            VectorSearchResult(
                chunk_id="c_1",
                paper_id="paper_vaswani",
                page_number=3,
                section_name="Model",
                text="The Transformer relies entirely on self-attention.",
                similarity_score=0.91,
                paper_title="Attention Is All You Need"
            )
        ]
        graph_triples = [
            GraphTripleItem(
                source="Transformer",
                relation_type="USES_METHOD",
                target="Self-Attention",
                description="Transformer uses self-attention",
                paper_id="paper_vaswani"
            )
        ]

        fused_items = HybridRetriever.apply_reciprocal_rank_fusion(
            vector_results=vector_res,
            graph_triples=graph_triples,
            vector_weight=1.0,
            graph_weight=1.0,
            rrf_k=60
        )
        assert len(fused_items) == 2

        sources = [
            {
                "paper_id": item.paper_id,
                "paper_title": "Attention Is All You Need",
                "page_number": item.metadata.get("page_number", 1) if item.metadata else 1,
                "text": item.content
            }
            for item in fused_items
        ]

        generated_answer = (
            "The Transformer model relies on self-attention mechanisms "
            "[Paper: paper_vaswani, Page: 3]."
        )

        badges = CitationGuard.extract_citation_badges(generated_answer, sources)
        assert len(badges) >= 1
        assert badges[0].paper_id == "paper_vaswani"
        assert badges[0].page_number == 3

    @pytest.mark.asyncio
    @patch("app.workers.paper_processing.Neo4jGraphBuilder.persist_paper_graph", new_callable=AsyncMock)
    async def test_worker_end_to_end_pipeline(self, mock_neo4j, sample_pdf_path):
        """Integration: PaperProcessingWorker coordinates PDFLoader, Chunker, Extractor, and Graph Builder."""
        mock_neo4j.return_value = True

        result = await PaperProcessingWorker.process_paper(
            paper_id="p_integration_001",
            file_path=sample_pdf_path,
            title="Integrated Attention Paper"
        )

        assert result["status"] == "COMPLETED"
        assert result["pages_count"] == 2
        assert result["chunks_count"] >= 2
        assert result["graph_entities"] >= 1
        assert result["graph_persisted"] is True
