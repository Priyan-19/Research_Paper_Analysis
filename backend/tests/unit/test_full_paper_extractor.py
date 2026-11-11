import pytest
from app.graph.extractor import GraphExtractor
from app.schemas.graph import KnowledgeGraphExtractionResult, GraphEntity, GraphRelationship, EntityType, RelationType


def run_coroutine(coro):
    """Executes a coroutine to completion without spinning up Windows loopback sockets."""
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value


class TestFullPaperExtractor:
    """Unit tests for full-paper chunk-based knowledge graph extraction and subgraph merging."""

    def test_merge_subgraphs_deduplication_and_provenance(self):
        """Verifies that merging subgraphs deduplicates entities, merges descriptions, and preserves provenance."""
        sub1 = KnowledgeGraphExtractionResult(
            entities=[
                GraphEntity(name="Transformer", type=EntityType.CONCEPT, description="Attention architecture", page_number=1, section_name="Introduction"),
                GraphEntity(name="BERT", type=EntityType.MODEL, description="Pretrained model", page_number=1, section_name="Introduction")
            ],
            relationships=[
                GraphRelationship(source_entity="BERT", target_entity="Transformer", relation_type=RelationType.USES_METHOD, page_number=1)
            ]
        )
        sub2 = KnowledgeGraphExtractionResult(
            entities=[
                GraphEntity(name="Transformer", type=EntityType.CONCEPT, description="Attention architecture with multi-head self-attention mechanisms", page_number=2, section_name="Architecture")
            ],
            relationships=[
                GraphRelationship(source_entity="BERT", target_entity="Transformer", relation_type=RelationType.USES_METHOD, page_number=2)
            ]
        )

        merged = GraphExtractor.merge_subgraphs([sub1, sub2], paper_id="paper_123", paper_title="Test Paper")

        assert len(merged.entities) == 2  # Transformer and BERT
        # Transformer entity should retain the longer description
        t_entity = next(e for e in merged.entities if e.name == "Transformer")
        assert "multi-head self-attention" in t_entity.description
        assert t_entity.page_number == 1  # Retains earliest page provenance

        # Deduplicates relationships
        assert len(merged.relationships) == 1
        assert merged.relationships[0].source_entity == "BERT"
        assert merged.relationships[0].target_entity == "Transformer"

    def test_extract_graph_empty_chunks(self):
        """Returns empty extraction result on empty chunks list."""
        res = run_coroutine(GraphExtractor.extract_graph_from_chunks([], "p1", "t1"))
        assert len(res.entities) == 0
        assert len(res.relationships) == 0
