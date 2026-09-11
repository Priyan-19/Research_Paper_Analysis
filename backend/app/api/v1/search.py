from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.embeddings.vector_store import VectorStoreService
from app.schemas.search import (
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResultItem,
    EmbeddingJobResponse,
    GraphSearchRequest,
    GraphSearchResponse,
    HybridSearchRequest,
    HybridSearchResponse
)
from app.rag.graph_retriever import GraphRetriever
from app.rag.hybrid_retriever import HybridRetriever

router = APIRouter(tags=["Search Engine"])


@router.post(
    "/search/vector",
    response_model=VectorSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Vector Search",
    description="Embeds a natural language query text and executes a pgvector similarity search against stored PDF text chunks."
)
async def search_vector(
    request: VectorSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    search_results = await VectorStoreService.search_vector_similarity(
        db=db,
        query_text=request.query,
        top_k=request.top_k,
        paper_id_filter=request.paper_id
    )

    # Apply optional score thresholding
    if request.score_threshold is not None:
        search_results = [r for r in search_results if r.similarity_score >= request.score_threshold]

    items = [
        VectorSearchResultItem(
            chunk_id=r.chunk_id,
            paper_id=r.paper_id,
            page_number=r.page_number,
            section_name=r.section_name,
            text=r.text,
            similarity_score=r.similarity_score
        )
        for r in search_results
    ]

    return VectorSearchResponse(
        query=request.query,
        total_results=len(items),
        results=items
    )


@router.post(
    "/search/graph",
    response_model=GraphSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Knowledge Graph Relational Search",
    description="Extracts target entities from query, canonicalizes terms, traverses Neo4j graph nodes & edges up to max_depth, and returns relational triples."
)
async def search_graph(
    request: GraphSearchRequest
):
    return await GraphRetriever.search_graph(
        query=request.query,
        paper_id=request.paper_id,
        top_k=request.top_k,
        max_depth=request.max_depth
    )


@router.post(
    "/search/hybrid",
    response_model=HybridSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Hybrid Vector + Knowledge Graph RRF Search",
    description="Executes Vector Search and Graph Search concurrently, applies Reciprocal Rank Fusion (RRF) scoring, and synthesizes a unified hybrid evidence context."
)
async def search_hybrid(
    request: HybridSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    return await HybridRetriever.search_hybrid(
        db=db,
        query=request.query,
        paper_id=request.paper_id,
        top_k=request.top_k,
        vector_weight=request.vector_weight,
        graph_weight=request.graph_weight,
        rrf_k=request.rrf_k
    )


@router.post(
    "/papers/{paper_id}/embed",
    response_model=EmbeddingJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Vector Embeddings for a Paper",
    description="Manually triggers dense vector embedding generation for all text chunks of a specific paper."
)
async def embed_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    embedded_count = await VectorStoreService.embed_paper_chunks(db=db, paper_id=paper_id)
    return EmbeddingJobResponse(
        paper_id=paper_id,
        chunks_embedded=embedded_count,
        status="COMPLETED",
        message=f"Successfully generated and stored embeddings for {embedded_count} chunks."
    )


