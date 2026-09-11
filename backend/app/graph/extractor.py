import re
from typing import List, Optional
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
    Extracts structured entities and relationships from research text passages.
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
    async def extract_graph_from_text(
        cls,
        text: str,
        paper_id: str,
        paper_title: str
    ) -> KnowledgeGraphExtractionResult:
        """
        Extracts entities and relationships from a text snippet using structured LLM output.
        """
        if not text or not text.strip():
            return KnowledgeGraphExtractionResult(entities=[], relationships=[])

        prompt = (
            f"PAPER TITLE: {paper_title}\n"
            f"TEXT PASSAGE:\n{text[:2000]}\n\n"
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
            # Canonicalize extracted result
            return EntityCanonicalizer.canonicalize_graph(raw_extraction)

        except Exception as e:
            logger.warning(f"LLM Graph Extraction failed for paper {paper_id}, using rule fallback: {str(e)}")
            return cls._fallback_extraction(text, paper_title)

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
