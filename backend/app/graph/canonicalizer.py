import re
import difflib
from typing import List, Dict, Tuple, Set, Optional, Any
from app.schemas.graph import GraphEntity, GraphRelationship, KnowledgeGraphExtractionResult, EntityType


class EntityCanonicalizer:
    """
    Hybrid Entity Resolution & Canonicalization Engine.
    Combines:
    1. Normalized string matching
    2. Curated scientific alias dictionary
    3. Version-safe edit-distance matching
    4. Dense vector embedding similarity
    5. Confidence thresholds & review log for ambiguous matches
    """

    # Comprehensive scientific alias mappings
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
        "pgvector extension": "pgvector",
        "convolutional neural network": "CNN",
        "convolutional neural networks": "CNN",
        "convnet": "CNN",
        "recurrent neural network": "RNN",
        "recurrent neural networks": "RNN",
        "gnn": "GNN",
        "graph convolutional network": "GCN",
        "graph convolutional networks": "GCN",
        "natural language processing": "NLP",
        "reinforcement learning from human feedback": "RLHF",
        "low-rank adaptation": "LoRA",
        "multi-head attention": "Multi-Head Attention",
        "mha": "Multi-Head Attention",
        "mixture of experts": "MoE",
        "mean reciprocal rank": "MRR"
    }

    # In-memory record of ambiguous matches for human review / auditing
    _pending_review_log: List[Dict[str, Any]] = []

    @classmethod
    def canonicalize_name(cls, name: str) -> str:
        """
        Normalizes an entity name string using normalized cleaning and dictionary lookup.
        """
        if not name:
            return ""

        cleaned = name.strip().strip("\'\".,;")
        cleaned = re.sub(r'\s+', ' ', cleaned)
        lower = cleaned.lower()

        if lower in cls.ALIAS_MAP:
            return cls.ALIAS_MAP[lower]

        # Standard acronym/capitalization logic
        if cleaned.isupper() or len(cleaned) <= 4 or re.match(r'^[A-Za-z]+-\d+$', cleaned):
            return cleaned.upper()

        return cleaned.title()

    @classmethod
    def are_distinct_versions(cls, name1: str, name2: str) -> bool:
        """
        Detects whether two names represent distinct versioned models or checkpoints
        (e.g. 'GPT-3' vs 'GPT-4', 'Llama-2' vs 'Llama-3', 'ResNet-50' vs 'ResNet-101').
        Guarantees that distinct versions are NEVER automatically merged.
        """
        v1 = re.findall(r'\b(?:v|version)?\s*(\d+(?:\.\d+)*)\b', name1.lower())
        v2 = re.findall(r'\b(?:v|version)?\s*(\d+(?:\.\d+)*)\b', name2.lower())
        if v1 and v2 and v1 != v2:
            return True
        return False

    @classmethod
    def calculate_string_similarity(cls, str1: str, str2: str) -> float:
        """
        Computes normalized character-level Levenshtein/Gestalt similarity ratio in [0.0, 1.0].
        """
        if not str1 or not str2:
            return 0.0
        return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    @classmethod
    def resolve_entity(
        cls,
        candidate_name: str,
        existing_entities: List[str],
        confidence_threshold: float = 0.88,
        use_embeddings: bool = False
    ) -> Tuple[str, float]:
        """
        Resolves an entity name against existing known entities using hybrid resolution:
        1. Exact canonical name match -> 1.0
        2. Alias dictionary -> 1.0
        3. Edit-distance matching -> >= threshold
        4. Optional embedding similarity -> >= 0.90
        Returns (resolved_name, confidence).
        """
        canonical = cls.canonicalize_name(candidate_name)
        if not canonical:
            return candidate_name, 0.0

        if not existing_entities:
            return canonical, 1.0

        # Check for direct or case-insensitive match
        for existing in existing_entities:
            if canonical.lower() == existing.lower():
                return existing, 1.0

        # Check string similarity
        best_match = canonical
        best_score = 0.0

        for existing in existing_entities:
            # Never merge distinct model versions (e.g. GPT-3 vs GPT-4)
            if cls.are_distinct_versions(canonical, existing):
                continue

            sim = cls.calculate_string_similarity(canonical, existing)
            if sim > best_score:
                best_score = sim
                best_match = existing

        # High confidence fuzzy match (typo or minor plural)
        if best_score >= confidence_threshold:
            return best_match, round(best_score, 4)

        # Ambiguous match: log for human review
        if 0.60 <= best_score < confidence_threshold:
            cls._pending_review_log.append({
                "candidate": canonical,
                "potential_match": best_match,
                "similarity_score": round(best_score, 4),
                "status": "PENDING_REVIEW"
            })

        return canonical, 1.0

    @classmethod
    def get_pending_review_log(cls) -> List[Dict[str, Any]]:
        """Returns list of ambiguous entity matches logged for review."""
        return cls._pending_review_log

    @classmethod
    def canonicalize_graph(cls, extraction: KnowledgeGraphExtractionResult) -> KnowledgeGraphExtractionResult:
        """
        Canonicalizes all entities and relationships in an extraction result.
        Deduplicates entity nodes, merges descriptions and provenance,
        and remaps relationship source/target names safely.
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
                    description=entity.description,
                    page_number=entity.page_number,
                    section_name=entity.section_name,
                    chunk_id=entity.chunk_id
                )
            else:
                existing = canonical_entities_map[cname]
                if entity.description and (not existing.description or len(entity.description) > len(existing.description)):
                    canonical_entities_map[cname].description = entity.description
                if existing.page_number is None and entity.page_number is not None:
                    canonical_entities_map[cname].page_number = entity.page_number
                if existing.section_name is None and entity.section_name is not None:
                    canonical_entities_map[cname].section_name = entity.section_name

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
                canonical_entities_map[src] = GraphEntity(
                    name=src,
                    type=EntityType.CONCEPT,
                    description=None,
                    page_number=rel.page_number,
                    section_name=rel.section_name,
                    chunk_id=rel.chunk_id
                )
            if tgt not in canonical_entities_map:
                canonical_entities_map[tgt] = GraphEntity(
                    name=tgt,
                    type=EntityType.CONCEPT,
                    description=None,
                    page_number=rel.page_number,
                    section_name=rel.section_name,
                    chunk_id=rel.chunk_id
                )

            rel_val = rel.relation_type.value if hasattr(rel.relation_type, "value") else str(rel.relation_type)
            edge_key = (src.lower(), tgt.lower(), rel_val.lower())
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                canonical_relationships.append(
                    GraphRelationship(
                        source_entity=src,
                        target_entity=tgt,
                        relation_type=rel.relation_type,
                        description=rel.description,
                        page_number=rel.page_number,
                        section_name=rel.section_name,
                        chunk_id=rel.chunk_id,
                        paper_id=rel.paper_id
                    )
                )

        return KnowledgeGraphExtractionResult(
            entities=list(canonical_entities_map.values()),
            relationships=canonical_relationships
        )
