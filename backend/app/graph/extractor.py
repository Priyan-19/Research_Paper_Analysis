import re
from typing import List, Optional, Dict, Any
from app.core.logging import logger
from app.llm import get_llm_provider
from app.schemas.graph import (
    KnowledgeGraphExtractionResult,
    GraphEntity,
    GraphRelationship,
    EntityType,
    RelationType
)
from app.graph.canonicalizer import EntityCanonicalizer


class GraphExtractor:
    """
    LLM-powered Knowledge Graph Extraction Engine.
    Extracts structured entities and relationships from research text passages,
    supporting full-paper chunk-based extraction, provenance preservation, and subgraph merging.
    """

    EXTRACTION_SYSTEM_PROMPT = """You are an expert Knowledge Graph Extraction AI.
Your objective is to read scientific research passages and extract all key research entities and directed relationships.

ENTITY TYPES TO EXTRACT:
- CONCEPT: Core research ideas, paradigms, or theories (e.g. "RAG", "Attention Mechanism")
- METHOD: Algorithms, architectures, or techniques (e.g. "Sentence Transformers", "PyMuPDF")
- DATASET: Benchmarks or training datasets (e.g. "GLUE", "SQuAD")
- METRIC: Quantitative evaluation metrics (e.g. "Accuracy", "F1 Score", "Cosine Distance")
- AUTHOR: Researchers or authors (e.g. "Harrison Chase")
- TASK: Natural language or AI tasks (e.g. "Question Answering", "Sentiment Analysis")
- MODEL: AI/ML model checkpoints (e.g. "all-MiniLM-L6-v2", "Gemini 1.5 Flash")
- TOOL: Software libraries or frameworks (e.g. "LangChain", "FastAPI", "Neo4j", "pgvector")

RELATIONSHIP TYPES:
- USES_METHOD: Entity A uses algorithm/tool Entity B
- EVALUATED_ON: Method A evaluated on Dataset B
- PROPOSES: Paper/Author A introduces Method/Concept B
- APPLIES_TO: Method A applies to Task B
- AUTHORED_BY: Paper A written by Author B
- ACHIEVES_METRIC: Method A achieves Metric B
- EXTENDS: Method A builds upon or extends Method B

INSTRUCTIONS:
1. Extract concise entity names (1-4 words max).
2. Avoid generic pronouns or vague words.
3. Ensure every relationship connects valid entities present in the entity list.
"""

    @classmethod
    async def extract_graph_from_chunks(
        cls,
        chunks: List[Any],
        paper_id: str,
        paper_title: str,
        window_size: int = 3,
        window_overlap: int = 1
    ) -> KnowledgeGraphExtractionResult:
        """
        Extracts entities and relationships from complete paper chunks using a sliding window.
        Merges subgraphs, deduplicates entities/relationships, and preserves page and section provenance.
        """
        if not chunks:
            return KnowledgeGraphExtractionResult(entities=[], relationships=[])

        all_extracted_subgraphs: List[KnowledgeGraphExtractionResult] = []
        base_step = max(1, window_size - window_overlap)
        max_windows = 15
        step = max(base_step, len(chunks) // max_windows) if len(chunks) > 20 else base_step
        rate_limited = False

        for i in range(0, len(chunks), step):
            window_chunks = chunks[i:i + window_size]
            if not window_chunks:
                continue

            # Extract window metadata
            first_chunk = window_chunks[0]
            page_num = getattr(first_chunk, "page_number", None) or (first_chunk.get("page_number") if isinstance(first_chunk, dict) else None)
            section = getattr(first_chunk, "section_name", None) or (first_chunk.get("section_name") if isinstance(first_chunk, dict) else "General")
            chunk_id = getattr(first_chunk, "id", None) or getattr(first_chunk, "chunk_id", None) or (first_chunk.get("chunk_id") if isinstance(first_chunk, dict) else None)

            # Combine window texts
            texts = []
            for c in window_chunks:
                t = getattr(c, "text", None) or (c.get("text") if isinstance(c, dict) else str(c))
                if t:
                    texts.append(t)
            combined_text = "\n\n".join(texts).strip()

            if not combined_text:
                continue

            # Extract graph from this window (truncate to safe window context if necessary)
            snippet = combined_text[:3500]
            prompt = (
                f"PAPER TITLE: {paper_title}\n"
                f"SECTION: {section} (Page {page_num or 'N/A'})\n"
                f"TEXT PASSAGE:\n{snippet}\n\n"
                f"Extract all scientific entities and directed relationships from this passage."
            )

            if not rate_limited:
                try:
                    llm = get_llm_provider()
                    raw_extraction = await llm.generate_structured(
                        prompt=prompt,
                        response_schema=KnowledgeGraphExtractionResult,
                        system_prompt=cls.EXTRACTION_SYSTEM_PROMPT,
                        temperature=0.1
                    )
                except Exception as e:
                    logger.warning(f"Chunk window {i} LLM extraction failed: {str(e)}; falling back to heuristic")
                    if "rate limit" in str(e).lower() or "429" in str(e):
                        rate_limited = True
                    raw_extraction = cls._fallback_extraction(snippet, paper_title)
            else:
                raw_extraction = cls._fallback_extraction(snippet, paper_title)

            # Attach provenance to extracted items
            for ent in raw_extraction.entities:
                if ent.page_number is None:
                    ent.page_number = page_num
                if ent.section_name is None:
                    ent.section_name = section
                if ent.chunk_id is None and chunk_id:
                    ent.chunk_id = str(chunk_id)

            for rel in raw_extraction.relationships:
                if rel.page_number is None:
                    rel.page_number = page_num
                if rel.section_name is None:
                    rel.section_name = section
                if rel.chunk_id is None and chunk_id:
                    rel.chunk_id = str(chunk_id)
                if rel.paper_id is None:
                    rel.paper_id = paper_id

            all_extracted_subgraphs.append(raw_extraction)

        return cls.merge_subgraphs(all_extracted_subgraphs, paper_id, paper_title)

    @classmethod
    def merge_subgraphs(
        cls,
        subgraphs: List[KnowledgeGraphExtractionResult],
        paper_id: str = "",
        paper_title: str = ""
    ) -> KnowledgeGraphExtractionResult:
        """
        Combines multiple extracted subgraphs, deduplicates nodes, merges descriptions,
        and consolidates relationships.
        """
        merged_entities: Dict[str, GraphEntity] = {}
        merged_relationships: List[GraphRelationship] = []
        seen_edges = set()

        for sub in subgraphs:
            for ent in sub.entities:
                key = EntityCanonicalizer.canonicalize_name(ent.name)
                if not key:
                    continue
                if key not in merged_entities:
                    merged_entities[key] = GraphEntity(
                        name=key,
                        type=ent.type,
                        description=ent.description,
                        page_number=ent.page_number,
                        section_name=ent.section_name,
                        chunk_id=ent.chunk_id
                    )
                else:
                    existing = merged_entities[key]
                    if ent.description and (not existing.description or len(ent.description) > len(existing.description)):
                        existing.description = ent.description
                    if existing.page_number is None and ent.page_number is not None:
                        existing.page_number = ent.page_number

            for rel in sub.relationships:
                src = EntityCanonicalizer.canonicalize_name(rel.source_entity)
                tgt = EntityCanonicalizer.canonicalize_name(rel.target_entity)
                if not src or not tgt or src == tgt:
                    continue

                edge_key = (src.lower(), str(rel.relation_type).lower(), tgt.lower())
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    merged_relationships.append(
                        GraphRelationship(
                            source_entity=src,
                            target_entity=tgt,
                            relation_type=rel.relation_type,
                            description=rel.description,
                            page_number=rel.page_number,
                            section_name=rel.section_name,
                            chunk_id=rel.chunk_id,
                            paper_id=rel.paper_id or paper_id
                        )
                    )

        combined_result = KnowledgeGraphExtractionResult(
            entities=list(merged_entities.values()),
            relationships=merged_relationships
        )
        return EntityCanonicalizer.canonicalize_graph(combined_result)

    @classmethod
    async def extract_graph_from_text(
        cls,
        text: str,
        paper_id: str,
        paper_title: str
    ) -> KnowledgeGraphExtractionResult:
        """
        Extracts entities and relationships from text.
        For longer papers, automatically splits into chunks to extract across the full content.
        """
        if not text or not text.strip():
            return KnowledgeGraphExtractionResult(entities=[], relationships=[])

        # If text is small (<3000 chars), process directly
        if len(text) <= 3000:
            prompt = (
                f"PAPER TITLE: {paper_title}\n"
                f"TEXT PASSAGE:\n{text}\n\n"
                f"Extract all scientific entities and directed relationships from this text passage."
            )
            try:
                llm = get_llm_provider()
                raw_extraction = await llm.generate_structured(
                    prompt=prompt,
                    response_schema=KnowledgeGraphExtractionResult,
                    system_prompt=cls.EXTRACTION_SYSTEM_PROMPT,
                    temperature=0.1
                )
                for ent in raw_extraction.entities:
                    if ent.page_number is None:
                        ent.page_number = 1
                for rel in raw_extraction.relationships:
                    if rel.paper_id is None:
                        rel.paper_id = paper_id
                return EntityCanonicalizer.canonicalize_graph(raw_extraction)
            except Exception as e:
                logger.warning(f"LLM Graph Extraction failed for paper {paper_id}, using rule fallback: {str(e)}")
                return cls._fallback_extraction(text, paper_title)

        # For longer text, chunk it into overlapping segments and merge
        chunk_size = 2000
        overlap = 300
        text_chunks = []
        start = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            text_chunks.append({"text": text[start:end], "page_number": 1, "section_name": "General"})
            if end >= len(text):
                break
            start += chunk_size - overlap

        return await cls.extract_graph_from_chunks(
            chunks=text_chunks,
            paper_id=paper_id,
            paper_title=paper_title
        )

    @classmethod
    async def extract_graph(
        cls,
        text: str,
        paper_title: str = "",
        paper_id: str = ""
    ) -> KnowledgeGraphExtractionResult:
        """Alias for extract_graph_from_text."""
        return await cls.extract_graph_from_text(text=text, paper_id=paper_id, paper_title=paper_title)

    @classmethod
    def _fallback_extraction(cls, text: str, paper_title: str) -> KnowledgeGraphExtractionResult:
        """
        Domain-agnostic heuristic extraction for general scientific research papers across any field.
        """
        entities = []
        relationships = []

        # 1. Add Paper Entity
        title_entity = EntityCanonicalizer.canonicalize_name(paper_title or "Research Paper")
        if title_entity:
            entities.append(GraphEntity(name=title_entity, type=EntityType.CONCEPT, description="Research Paper"))

        # 2. Extract technical terms / capitalized phrases dynamically from text
        pattern = r'\b([A-Z][a-zA-Z0-9\-\_]{2,}(?:\s+[A-Z][a-zA-Z0-9\-\_]{2,}){0,3})\b'
        candidates = re.findall(pattern, text)

        stopwords = {
            "The", "This", "That", "These", "Those", "Abstract", "Introduction", "Conclusion",
            "Method", "Results", "Discussion", "Figure", "Table", "Page", "Section", "Paper",
            "Study", "Author", "Authors", "Using", "From", "With", "After", "Before", "HTTP", "URL"
        }

        extracted_terms = []
        seen = set()
        for term in candidates:
            term_clean = term.strip()
            if len(term_clean) > 3 and term_clean not in stopwords and not term_clean.isnumeric():
                cname = EntityCanonicalizer.canonicalize_name(term_clean)
                if cname and cname not in seen and cname != title_entity:
                    seen.add(cname)
                    entities.append(GraphEntity(name=cname, type=EntityType.CONCEPT, description="Extracted Scientific Concept"))
                    extracted_terms.append(cname)
                    if len(extracted_terms) >= 20:
                        break

        # 3. Create relationships connecting paper to extracted concepts
        for term_name in extracted_terms:
            if title_entity and title_entity != term_name:
                relationships.append(
                    GraphRelationship(
                        source_entity=title_entity,
                        target_entity=term_name,
                        relation_type=RelationType.USES_METHOD,
                        description=f"Paper investigates or utilizes {term_name}"
                    )
                )

        raw_result = KnowledgeGraphExtractionResult(entities=entities, relationships=relationships)
        return EntityCanonicalizer.canonicalize_graph(raw_result)
