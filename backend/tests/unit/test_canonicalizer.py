import pytest
from app.graph.canonicalizer import EntityCanonicalizer
from app.schemas.graph import (
    KnowledgeGraphExtractionResult,
    GraphEntity,
    GraphRelationship,
    EntityType,
    RelationType
)


class TestEntityCanonicalizer:
    """Unit tests for entity name normalization, alias resolution, and deduplication."""

    @pytest.mark.parametrize("raw_name,expected", [
        ("retrieval augmented generation", "RAG"),
        ("Retrieval-Augmented Generation", "RAG"),
        ("large language model", "LLM"),
        ("LLMs", "LLM"),
        ("bidirectional encoder representations from transformers", "BERT"),
        ("bert model", "BERT"),
        ("generative pre-trained transformer", "GPT"),
        ("gpt model", "GPT"),
        ("knowledge graph", "Knowledge Graph"),
        ("pgvector extension", "pgvector"),
    ])
    def test_canonicalize_alias_map(self, raw_name, expected):
        """Resolves known synonymous variants to their canonical standard."""
        assert EntityCanonicalizer.canonicalize_name(raw_name) == expected

    def test_canonicalize_strip_punctuation(self):
        """Strips trailing punctuation, quotes, and whitespace."""
        assert EntityCanonicalizer.canonicalize_name('  "Graph Neural Network";  ') == "Graph Neural Network"
        assert EntityCanonicalizer.canonicalize_name("   'Transformer'.   ") == "Transformer"

    def test_canonicalize_empty_input(self):
        """Handles empty or None strings safely."""
        assert EntityCanonicalizer.canonicalize_name("") == ""
        assert EntityCanonicalizer.canonicalize_name(None) == ""

    def test_canonicalize_graph_deduplication(self):
        """Merges duplicate entities with different aliases and rewires relationship targets."""
        raw_result = KnowledgeGraphExtractionResult(
            entities=[
                GraphEntity(name="retrieval augmented generation", type=EntityType.CONCEPT, description="Desc 1"),
                GraphEntity(name="RAG", type=EntityType.CONCEPT, description="Desc 2"),
                GraphEntity(name="large language model", type=EntityType.CONCEPT, description="Desc 3")
            ],
            relationships=[
                GraphRelationship(
                    source_entity="retrieval augmented generation",
                    target_entity="large language model",
                    relation_type=RelationType.USES_METHOD
                ),
                GraphRelationship(
                    source_entity="RAG",
                    target_entity="LLM",
                    relation_type=RelationType.USES_METHOD
                )
            ]
        )

        canonical_result = EntityCanonicalizer.canonicalize_graph(raw_result)

        assert len(canonical_result.entities) == 2
        entity_names = {e.name for e in canonical_result.entities}
        assert entity_names == {"RAG", "LLM"}

        assert len(canonical_result.relationships) == 1
        assert canonical_result.relationships[0].source_entity == "RAG"
        assert canonical_result.relationships[0].target_entity == "LLM"
