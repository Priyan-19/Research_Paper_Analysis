import re
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from app.core.logging import logger
from app.database.neo4j import get_neo4j_session
from app.graph.canonicalizer import EntityCanonicalizer
from app.llm import get_llm_provider
from app.schemas.search import (
    GraphSearchResponse,
    GraphTripleItem,
    ConnectedPaperItem
)


class QueryEntitiesResult(BaseModel):
    entities: List[str] = Field(default_factory=list, description="Extracted entity names from user query")


class QueryEntityExtractor:
    """
    LLM and Heuristic Extractor to identify key research entities, algorithms, models,
    datasets, and methods from user questions.
    """

    SYSTEM_PROMPT = """You are an expert NLP Entity Extraction system for scientific research questions.
Given a user's question, extract all specific research entities, models, methods, datasets, algorithms, authors, or tasks.
Output a JSON list of entity names (1-4 words max per entity).
Do not extract generic question words like "what", "which", "paper", "method", "results", "how".
Example:
Input: "Which models were evaluated on the GLUE benchmark using BERT?"
Output entities: ["GLUE", "BERT"]
"""

    @classmethod
    async def extract_query_entities(cls, query: str) -> List[str]:
        """
        Extracts and canonicalizes entities from a natural language user query.
        """
        if not query or not query.strip():
            return []

        entities: List[str] = []

        # 1. Try LLM Structured Extraction
        try:
            llm = get_llm_provider()
            prompt = f"Extract all research entities from the following user question:\n\"{query}\""
            result: QueryEntitiesResult = await llm.generate_structured(
                prompt=prompt,
                response_schema=QueryEntitiesResult,
                system_prompt=cls.SYSTEM_PROMPT,
                temperature=0.0
            )
            entities = result.entities
        except Exception as e:
            logger.warning(f"LLM Query Entity Extraction failed, falling back to heuristics: {str(e)}")
            entities = cls._heuristic_extraction(query)

        # 2. Fallback heuristic check if LLM returned empty list
        if not entities:
            entities = cls._heuristic_extraction(query)

        # 3. Canonicalize each extracted entity name
        canonicalized_entities: List[str] = []
        seen = set()
        for ent in entities:
            cname = EntityCanonicalizer.canonicalize_name(ent)
            if cname and cname.lower() not in seen:
                canonicalized_entities.append(cname)
                seen.add(cname.lower())

        return canonicalized_entities

    @classmethod
    def _heuristic_extraction(cls, query: str) -> List[str]:
        """
        Rule-based keyword fallback extractor for query entities.
        """
        found = []

        # Known academic/tech domain keywords
        domain_keywords = [
            "BERT", "GPT", "LLM", "RAG", "Transformer", "Attention", "Sentence Transformers",
            "GLUE", "SQuAD", "MNIST", "ImageNet", "PostgreSQL", "pgvector", "Neo4j", "FastAPI",
            "React", "PyTorch", "TensorFlow", "LangChain", "Llama", "Gemini", "PyMuPDF", "Ollama"
        ]

        query_lower = query.lower()
        for kw in domain_keywords:
            if kw.lower() in query_lower:
                found.append(kw)

        # Extract capitalized words (excluding start of sentence if single common word)
        words = re.findall(r'\b[A-Z][a-zA-Z0-9_\-]+\b', query)
        stop_words = {"What", "Which", "How", "Why", "Who", "Where", "When", "Is", "Are", "Can", "Could", "Does", "Do", "The", "A", "An", "In", "On"}
        for w in words:
            if w not in stop_words and w not in found:
                found.append(w)

        return found


class GraphRetriever:
    """
    Knowledge Graph Retrieval Service.
    Traverses Neo4j graph nodes and relationships to retrieve relational context for natural language questions.
    """

    @classmethod
    async def search_graph(
        cls,
        query: str,
        paper_id: Optional[str] = None,
        top_k: int = 10,
        max_depth: int = 2
    ) -> GraphSearchResponse:
        """
        Main entrypoint for Knowledge Graph Retrieval.
        Extracts query entities, queries Neo4j for 1-hop and 2-hop connected graph triples,
        fetches connected papers, and formats context string.
        """
        # Step 1: Extract and canonicalize entities from query
        matched_entities = await QueryEntityExtractor.extract_query_entities(query)
        logger.info(f"Graph Search extracted query entities: {matched_entities} from query: '{query}'")

        if not matched_entities:
            return GraphSearchResponse(
                query=query,
                matched_entities=[],
                total_triples=0,
                triples=[],
                connected_papers=[],
                formatted_graph_context="No specific research entities identified in the query for graph retrieval."
            )

        # Step 2: Query Neo4j for connected graph triples and papers
        triples, connected_papers = await cls._traverse_neo4j(
            entities=matched_entities,
            paper_id_filter=paper_id,
            max_depth=max_depth,
            top_k=top_k
        )

        # Step 3: Format graph context string for RAG ingestion
        formatted_context = cls.build_formatted_graph_context(triples, connected_papers)

        return GraphSearchResponse(
            query=query,
            matched_entities=matched_entities,
            total_triples=len(triples),
            triples=triples,
            connected_papers=connected_papers,
            formatted_graph_context=formatted_context
        )

    @classmethod
    async def _traverse_neo4j(
        cls,
        entities: List[str],
        paper_id_filter: Optional[str] = None,
        max_depth: int = 2,
        top_k: int = 10
    ) -> tuple[List[GraphTripleItem], List[ConnectedPaperItem]]:
        """
        Executes Cypher graph traversals against Neo4j to pull relationship edges and paper nodes.
        """
        triples: List[GraphTripleItem] = []
        connected_papers_dict: Dict[str, ConnectedPaperItem] = {}

        if not entities:
            return [], []

        # Convert entities to lowercase set for flexible matching
        entity_patterns = [e.lower() for e in entities]

        async with get_neo4j_session() as session:
            # 1. Query Relationship Edges (1-Hop Traversal)
            query_1hop = """
            MATCH (src:Entity)-[r]->(tgt:Entity)
            WHERE (toLower(src.name) IN $entity_patterns OR toLower(tgt.name) IN $entity_patterns)
              AND type(r) <> 'MENTIONS'
            """
            if paper_id_filter:
                query_1hop += " AND (r.paper_id = $paper_id OR r.paper_id IS NULL)"

            query_1hop += """
            RETURN src.name AS source, type(r) AS rel_type, tgt.name AS target, r.description AS description, r.paper_id AS paper_id
            LIMIT $limit
            """

            try:
                result_1hop = await session.run(query_1hop, entity_patterns=entity_patterns, paper_id=paper_id_filter, limit=top_k)
                async for record in result_1hop:
                    triples.append(
                        GraphTripleItem(
                            source=record["source"],
                            relation_type=record["rel_type"],
                            target=record["target"],
                            description=record["description"],
                            paper_id=record["paper_id"]
                        )
                    )
            except Exception as e:
                logger.error(f"Neo4j Cypher 1-hop traversal failed: {str(e)}")

            # 2. Query 2-Hop Traversal if 1-hop yielded fewer than top_k items and max_depth >= 2
            if len(triples) < top_k and max_depth >= 2:
                remaining_limit = top_k - len(triples)
                query_2hop = """
                MATCH (src:Entity)-[r1]->(mid:Entity)-[r2]->(tgt:Entity)
                WHERE (toLower(src.name) IN $entity_patterns OR toLower(tgt.name) IN $entity_patterns)
                  AND type(r1) <> 'MENTIONS' AND type(r2) <> 'MENTIONS'
                RETURN src.name AS source, type(r1) AS rel_type_1, mid.name AS mid_name, type(r2) AS rel_type_2, tgt.name AS target, r2.description AS description, r2.paper_id AS paper_id
                LIMIT $limit
                """
                try:
                    result_2hop = await session.run(query_2hop, entity_patterns=entity_patterns, limit=remaining_limit)
                    async for record in result_2hop:
                        # Append 2-hop triple leg
                        triples.append(
                            GraphTripleItem(
                                source=record["mid_name"],
                                relation_type=record["rel_type_2"],
                                target=record["target"],
                                description=record["description"],
                                paper_id=record["paper_id"]
                            )
                        )
                except Exception as e:
                    logger.error(f"Neo4j Cypher 2-hop traversal failed: {str(e)}")

            # 3. Query Connected Papers mentioning target entities
            query_papers = """
            MATCH (p:Paper)-[:MENTIONS]->(e:Entity)
            WHERE toLower(e.name) IN $entity_patterns
            """
            if paper_id_filter:
                query_papers += " AND p.id = $paper_id"

            query_papers += """
            RETURN p.id AS paper_id, p.title AS title, count(distinct e) AS cnt
            ORDER BY cnt DESC
            LIMIT 10
            """

            try:
                result_papers = await session.run(query_papers, entity_patterns=entity_patterns, paper_id=paper_id_filter)
                async for record in result_papers:
                    pid = record["paper_id"]
                    connected_papers_dict[pid] = ConnectedPaperItem(
                        paper_id=pid,
                        paper_title=record["title"] or pid,
                        matched_entity_count=record["cnt"]
                    )
            except Exception as e:
                logger.error(f"Neo4j Cypher connected papers query failed: {str(e)}")

        return triples, list(connected_papers_dict.values())

    @classmethod
    def build_formatted_graph_context(
        cls,
        triples: List[GraphTripleItem],
        connected_papers: List[ConnectedPaperItem]
    ) -> str:
        """
        Formats graph triples and connected papers into a clean textual context string
        ready for LLM prompt augmentation.
        """
        if not triples and not connected_papers:
            return "No relevant Knowledge Graph facts or entity relationships were found in the database."

        lines = ["=== KNOWLEDGE GRAPH EVIDENCE & ENTITY RELATIONS ==="]

        if connected_papers:
            lines.append("\nRelevant Research Papers:")
            for p in connected_papers:
                lines.append(f"- Paper: '{p.paper_title}' (ID: {p.paper_id}) [Mentions {p.matched_entity_count} query entities]")

        if triples:
            lines.append("\nEntity Relationship Triples:")
            for t in triples:
                desc = f" ({t.description})" if t.description else ""
                pid = f" [Source Paper: {t.paper_id}]" if t.paper_id else ""
                lines.append(f"- ({t.source}) --[{t.relation_type}]--> ({t.target}){desc}{pid}")

        return "\n".join(lines)
