from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.services.paper_service import PaperService
from app.graph.extractor import GraphExtractor
from app.graph.neo4j_builder import Neo4jGraphBuilder
from app.graph.gnn_link_predictor import GNNLinkPredictor
from app.schemas.graph import (
    PaperGraphResponse,
    GraphStatsResponse,
    KnowledgeGraphExtractionResult,
    GNNPredictLinksRequest,
    GNNPredictLinksResponse,
    GNNLinkPredictionItem
)

router = APIRouter(prefix="/graph", tags=["Knowledge Graph Engine"])


@router.post(
    "/extract/{paper_id}",
    status_code=status.HTTP_200_OK,
    summary="Extract & Build Knowledge Graph for Research Paper",
    description="Parses paper text chunks, extracts research entities and directed relationships using LLM, canonicalizes entity names, and builds graph nodes/edges in Neo4j."
)
async def extract_paper_graph(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    paper = await PaperService.get_paper_by_id(db, paper_id)
    chunks = await PaperService.get_paper_chunks(db, paper_id)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No text chunks found for this paper. Please upload a valid PDF paper first."
        )

    # Combine representative text passages (Abstract + Introduction + Key Sections)
    sample_text = "\n\n".join([c.text for c in chunks[:10]])

    # 1. Extract Entities & Relationships
    extraction: KnowledgeGraphExtractionResult = await GraphExtractor.extract_graph_from_text(
        text=sample_text,
        paper_id=paper_id,
        paper_title=paper.title or paper.filename
    )

    # 2. Persist Graph to Neo4j
    await Neo4jGraphBuilder.persist_paper_graph(
        paper_id=paper_id,
        paper_title=paper.title or paper.filename,
        graph_data=extraction
    )

    return {
        "paper_id": paper_id,
        "paper_title": paper.title or paper.filename,
        "status": "COMPLETED",
        "entities_extracted": len(extraction.entities),
        "relationships_extracted": len(extraction.relationships),
        "message": f"Successfully extracted and saved Knowledge Graph for '{paper.filename}' to Neo4j."
    }


@router.get(
    "/paper/{paper_id}",
    response_model=PaperGraphResponse,
    summary="Get Knowledge Graph Subnetwork for a Paper",
    description="Retrieves all entity nodes and relationship edges associated with a specific research paper from Neo4j."
)
async def get_paper_graph(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    paper = await PaperService.get_paper_by_id(db, paper_id)
    return await Neo4jGraphBuilder.get_paper_graph(
        paper_id=paper_id,
        paper_title=paper.title or paper.filename
    )


@router.get(
    "/stats",
    response_model=GraphStatsResponse,
    summary="Get Global Knowledge Graph Statistics",
    description="Retrieves node counts, relationship counts, and entity/relationship type breakdowns across the Neo4j database."
)
async def get_graph_stats():
    return await Neo4jGraphBuilder.get_graph_stats()


@router.post(
    "/predict-links",
    response_model=GNNPredictLinksResponse,
    status_code=status.HTTP_200_OK,
    summary="GNN Graph Link Prediction Engine",
    description="Executes Graph Convolutional Network (GCN) embedding inference to rank prospective research links between source entity and candidate entities."
)
async def predict_graph_links(request: GNNPredictLinksRequest):
    formatted_rels = []
    if request.existing_relationships:
        for r in request.existing_relationships:
            if "source" in r and "target" in r:
                formatted_rels.append((r["source"], r["target"], r.get("relation", "USES_METHOD")))

    predictions = GNNLinkPredictor.predict_top_links(
        source_entity=request.source_entity,
        target_candidates=request.target_candidates,
        existing_relationships=formatted_rels,
        top_k=request.top_k
    )

    items = [
        GNNLinkPredictionItem(
            target_entity=p["target_entity"],
            link_probability=p["link_probability"],
            similarity_score=p["similarity_score"],
            gnn_recommendation=p["gnn_recommendation"]
        ) for p in predictions
    ]

    return GNNPredictLinksResponse(
        source_entity=request.source_entity,
        total_candidates_evaluated=len(request.target_candidates),
        predicted_links=items
    )
