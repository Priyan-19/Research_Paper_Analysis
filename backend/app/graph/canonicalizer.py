import re
from typing import List, Dict, Tuple, Set
from app.schemas.graph import GraphEntity, GraphRelationship, KnowledgeGraphExtractionResult


class EntityCanonicalizer:
    """
    Entity Resolution & Canonicalization Engine.
    Cleans, normalizes, and merges duplicate research entity names.
    """
    
    # Common entity alias mappings
    ALIAS_MAP = {
        "retrieval augmented generation": "RAG",
        "retrieval-augmented generation": "RAG",
        "large language model": "LLM",
        "large language models": "LLM",
        "llms": "LLM",
        "bidirectional encoder representations from transformers": "BERT",
        "bert model": "BERT",
        "b.e.r.t.": "BERT",
        "generative pre-trained transformer": "GPT",
        "gpt model": "GPT",
        "knowledge graph": "Knowledge Graph",
        "knowledge graphs": "Knowledge Graph",
        "langchain framework": "LangChain",
        "langchain library": "LangChain",
        "vector database": "Vector DB",
        "vector databases": "Vector DB",
        "pgvector extension": "pgvector"
    }

    @classmethod
    def canonicalize_name(cls, name: str) -> str:
        """
        Normalizes an entity name string.
        """
        if not name:
            return ""

        cleaned = name.strip().strip("\'\".,;")
        cleaned = re.sub(r'\s+', ' ', cleaned)
        lower = cleaned.lower()

        if lower in cls.ALIAS_MAP:
            return cls.ALIAS_MAP[lower]

        # Standard capitalization logic
        if lower.isupper() or len(cleaned) <= 4:
            return cleaned.upper()

        return cleaned.title()

    @classmethod
    def canonicalize_graph(cls, extraction: KnowledgeGraphExtractionResult) -> KnowledgeGraphExtractionResult:
        """
        Canonicalizes all entities and relationships in an extraction result.
        Deduplicates entity nodes and remaps relationship source/target names.
        """
        canonical_entities_map: Dict[str, GraphEntity] = {}

        # 1. Canonicalize and Merge Entities
        for entity in extraction.entities:
            cname = cls.canonicalize_name(entity.name)
            if not cname:
                continue

            if cname not in canonical_entities_map:
                canonical_entities_map[cname] = GraphEntity(
                    name=cname,
                    type=entity.type,
                    description=entity.description
                )
            else:
                # Retain longer description if available
                existing = canonical_entities_map[cname]
                if entity.description and (not existing.description or len(entity.description) > len(existing.description)):
                    canonical_entities_map[cname] = GraphEntity(
                        name=cname,
                        type=existing.type,
                        description=entity.description
                    )

        # 2. Canonicalize Relationships and Filter Invalid Edges
        canonical_relationships: List[GraphRelationship] = []
        seen_edges: Set[Tuple[str, str, str]] = set()

        for rel in extraction.relationships:
            src = cls.canonicalize_name(rel.source_entity)
            tgt = cls.canonicalize_name(rel.target_entity)

            if not src or not tgt or src == tgt:
                continue

            # Ensure both source and target exist in entities map
            if src not in canonical_entities_map:
                canonical_entities_map[src] = GraphEntity(name=src, type="CONCEPT", description=None)
            if tgt not in canonical_entities_map:
                canonical_entities_map[tgt] = GraphEntity(name=tgt, type="CONCEPT", description=None)

            edge_key = (src, tgt, rel.relation_type.value)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                canonical_relationships.append(
                    GraphRelationship(
                        source_entity=src,
                        target_entity=tgt,
                        relation_type=rel.relation_type,
                        description=rel.description
                    )
                )

        return KnowledgeGraphExtractionResult(
            entities=list(canonical_entities_map.values()),
            relationships=canonical_relationships
        )
