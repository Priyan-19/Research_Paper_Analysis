import pytest
from app.graph.canonicalizer import EntityCanonicalizer
from app.schemas.graph import KnowledgeGraphExtractionResult, GraphEntity, GraphRelationship, EntityType, RelationType


class TestHybridCanonicalizer:
    """Unit tests for hybrid entity resolution, version-safety, and canonicalization."""

    def test_version_protection_never_merges_checkpoints(self):
        """Verifies that model checkpoints with different numbers (e.g. GPT-3 vs GPT-4) are never merged."""
        assert EntityCanonicalizer.are_distinct_versions("GPT-3", "GPT-4") is True
        assert EntityCanonicalizer.are_distinct_versions("Llama 2", "Llama 3") is True
        assert EntityCanonicalizer.are_distinct_versions("ResNet-50", "ResNet-101") is True
        assert EntityCanonicalizer.are_distinct_versions("BERT", "BERT") is False
        assert EntityCanonicalizer.are_distinct_versions("Transformer", "Attention") is False

        resolved, conf = EntityCanonicalizer.resolve_entity("GPT-4", ["GPT-3"])
        assert resolved == "GPT-4"  # Remains distinct

    def test_alias_dictionary_expansion(self):
        """Verifies canonical alias mapping for scientific acronyms."""
        assert EntityCanonicalizer.canonicalize_name("retrieval augmented generation") == "RAG"
        assert EntityCanonicalizer.canonicalize_name("graph convolutional network") == "GCN"
        assert EntityCanonicalizer.canonicalize_name("convolutional neural network") == "CNN"
        assert EntityCanonicalizer.canonicalize_name("multi-head attention") == "Multi-Head Attention"

    def test_fuzzy_string_similarity_resolution(self):
        """Fuzzy matches slight typographical variations when above threshold."""
        existing = ["Sentence Transformers", "PostgreSQL"]
        resolved, score = EntityCanonicalizer.resolve_entity("Sentence Transformer", existing, confidence_threshold=0.85)
        assert resolved == "Sentence Transformers"
        assert score >= 0.85

    def test_ambiguous_match_logged_for_review(self):
        """Ambiguous matches with intermediate similarity are recorded in pending review log."""
        EntityCanonicalizer._pending_review_log.clear()
        EntityCanonicalizer.resolve_entity("Graph Neural Nets", ["Graph Networks"], confidence_threshold=0.95)
        log = EntityCanonicalizer.get_pending_review_log()
        assert len(log) >= 1
        assert log[0]["candidate"] == "Graph Neural Nets"
        assert log[0]["status"] == "PENDING_REVIEW"
