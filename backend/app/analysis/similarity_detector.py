from typing import List, Dict, Any, Optional, Set
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.services.paper_service import PaperService
from app.embeddings.vector_store import VectorStoreService, VectorSearchResult
from app.graph.neo4j_builder import Neo4jGraphBuilder
from app.schemas.graph import PaperGraphResponse
from app.schemas.analysis import (
    PaperSimilarityRequest,
    PaperSimilarityResponse,
    PaperSimilarityItem,
    SharedEntityBreakdown
)


class SimilarityDetector:
    """
    Research Paper Similarity & Duplicate Detection Engine.
    Computes a multi-factor weighted similarity score combining:
    - 40% Dense Vector Text Similarity
    - 20% Knowledge Graph Concept Overlap
    - 20% Knowledge Graph Method/Model Overlap
    - 20% Knowledge Graph Dataset Overlap
    """

    @classmethod
    async def check_paper_similarity(
        cls,
        db: AsyncSession,
        source_paper_id: str,
        target_paper_id: Optional[str] = None,
        top_k: int = 5
    ) -> PaperSimilarityResponse:
        """
        Calculates multi-factor similarity scores between a source paper and candidate target papers in the library.
        """
        logger.info(f"Computing paper similarity for source paper '{source_paper_id}' (target_filter={target_paper_id})")

        # Step 1: Verify source paper exists
        source_paper = await PaperService.get_paper_by_id(db, source_paper_id)
        if not source_paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source paper with ID '{source_paper_id}' was not found."
            )

        source_title = source_paper.title or source_paper.filename

        # Step 2: Fetch source paper text chunks for vector query
        source_chunks = await PaperService.get_paper_chunks(db, source_paper_id)
        sample_query = ""
        if source_chunks:
            sample_query = "\n".join([c.text for c in source_chunks[:3]])
        else:
            sample_query = source_title

        # Step 3: Perform Vector Similarity Search to find candidate papers
        vector_results: List[VectorSearchResult] = await VectorStoreService.search_vector_similarity(
            db=db,
            query_text=sample_query,
            top_k=top_k * 5,
            paper_id_filter=target_paper_id
        )

        # Group vector similarity scores by paper_id (selecting max similarity score per paper)
        paper_vector_sim: Dict[str, float] = {}
        for vr in vector_results:
            pid = vr.paper_id
            if pid.lower() == source_paper_id.lower():
                continue  # Exclude self-comparison
            if pid not in paper_vector_sim or vr.similarity_score > paper_vector_sim[pid]:
                paper_vector_sim[pid] = max(0.0, float(vr.similarity_score))

        # Handle specific target_paper_id request if target was not returned in vector search top-K
        if target_paper_id and target_paper_id.lower() not in paper_vector_sim and target_paper_id.lower() != source_paper_id.lower():
            paper_vector_sim[target_paper_id] = 0.0

        # Step 4: Fetch Knowledge Graph entities for source paper
        source_graph: PaperGraphResponse = await Neo4jGraphBuilder.get_paper_graph(
            paper_id=source_paper_id,
            paper_title=source_title
        )
        source_entities_by_type = cls._categorize_graph_entities(source_graph)

        # Step 5: Evaluate Multi-Factor Similarity for each candidate target paper
        similarity_items: List[PaperSimilarityItem] = []

        for target_id, v_sim in paper_vector_sim.items():
            target_paper = await PaperService.get_paper_by_id(db, target_id)
            target_title = (target_paper.title if target_paper and target_paper.title else f"Paper {target_id}")

            # Fetch target paper Knowledge Graph
            target_graph: PaperGraphResponse = await Neo4jGraphBuilder.get_paper_graph(
                paper_id=target_id,
                paper_title=target_title
            )
            target_entities_by_type = cls._categorize_graph_entities(target_graph)

            # Compute category overlap ratios and shared entity lists
            concept_sim, shared_concepts = cls._compute_jaccard_overlap(
                source_entities_by_type["concepts"],
                target_entities_by_type["concepts"]
            )
            method_sim, shared_methods = cls._compute_jaccard_overlap(
                source_entities_by_type["methods"],
                target_entities_by_type["methods"]
            )
            dataset_sim, shared_datasets = cls._compute_jaccard_overlap(
                source_entities_by_type["datasets"],
                target_entities_by_type["datasets"]
            )
            _, shared_models = cls._compute_jaccard_overlap(
                source_entities_by_type["models"],
                target_entities_by_type["models"]
            )

            # 4-Factor Weighted Overall Score
            # Formula: 0.40 * Vector_Sim + 0.20 * Concept_Overlap + 0.20 * Method_Overlap + 0.20 * Dataset_Overlap
            overall_score = round(
                0.40 * v_sim + 0.20 * concept_sim + 0.20 * method_sim + 0.20 * dataset_sim,
                4
            )

            # Assign Objective Classification Label
            if overall_score >= 0.75:
                label = "Highly Similar Research"
            elif overall_score >= 0.45:
                label = "Moderately Overlapping Research"
            else:
                label = "Low Overlap Research"

            similarity_items.append(
                PaperSimilarityItem(
                    paper_id=target_id,
                    paper_title=target_title,
                    overall_similarity_score=overall_score,
                    vector_similarity=round(v_sim, 4),
                    concept_overlap=round(concept_sim, 4),
                    method_overlap=round(method_sim, 4),
                    dataset_overlap=round(dataset_sim, 4),
                    classification_label=label,
                    shared_entities=SharedEntityBreakdown(
                        shared_concepts=shared_concepts,
                        shared_methods=shared_methods,
                        shared_datasets=shared_datasets,
                        shared_models=shared_models
                    )
                )
            )

        # Step 6: Sort by descending overall similarity score
        similarity_items.sort(key=lambda item: item.overall_similarity_score, reverse=True)
        top_matches = similarity_items[:top_k]

        return PaperSimilarityResponse(
            source_paper_id=source_paper_id,
            source_paper_title=source_title,
            total_matches=len(top_matches),
            matches=top_matches
        )

    @classmethod
    def _categorize_graph_entities(cls, graph_response: PaperGraphResponse) -> Dict[str, Set[str]]:
        """
        Categorizes graph nodes into entity type buckets for detailed overlap analysis.
        """
        buckets: Dict[str, Set[str]] = {
            "concepts": set(),
            "methods": set(),
            "models": set(),
            "datasets": set()
        }

        for n in graph_response.nodes:
            name_norm = n.name.strip().lower()
            ntype = str(n.type).upper()

            if ntype in ("CONCEPT", "TASK", "TOPIC", "METRIC"):
                buckets["concepts"].add(name_norm)
            elif ntype in ("METHOD", "TOOL"):
                buckets["methods"].add(name_norm)
            elif ntype == "MODEL":
                buckets["models"].add(name_norm)
                buckets["methods"].add(name_norm)
            elif ntype == "DATASET":
                buckets["datasets"].add(name_norm)
            else:
                buckets["concepts"].add(name_norm)

        return buckets

    @classmethod
    def _compute_jaccard_overlap(cls, set_a: Set[str], set_b: Set[str]) -> tuple[float, List[str]]:
        """
        Computes Jaccard similarity coefficient |A ∩ B| / |A ∪ B| and returns list of shared entity strings.
        """
        if not set_a and not set_b:
            return 0.0, []

        intersection = set_a.intersection(set_b)
        union = set_a.union(set_b)

        ratio = len(intersection) / len(union) if union else 0.0
        shared_list = sorted([s.title() for s in intersection])

        return ratio, shared_list
