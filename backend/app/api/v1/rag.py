from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.rag.vector_rag_service import VectorRAGService
from app.schemas.rag import VectorRAGRequest, VectorRAGResponse, RAGSourceItem

router = APIRouter(prefix="/rag", tags=["RAG Question Answering"])


@router.post(
    "/vector",
    response_model=VectorRAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Vector-Based Grounded RAG Question Answering",
    description="Retrieves Top-K semantically relevant PDF text passages, formats evidence context with page/section metadata, and generates an evidence-grounded research answer."
)
async def generate_vector_rag_answer(
    request: VectorRAGRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await VectorRAGService.generate_grounded_answer(
        db=db,
        query=request.query,
        top_k=request.top_k,
        paper_id=request.paper_id,
        temperature=request.temperature
    )

    sources = [
        RAGSourceItem(
            source_index=s["source_index"],
            paper_id=s["paper_id"],
            paper_title=s["paper_title"],
            page_number=s["page_number"],
            section_name=s["section_name"],
            chunk_id=s["chunk_id"],
            similarity_score=s["similarity_score"]
        )
        for s in result["sources"]
    ]

    return VectorRAGResponse(
        query=result["query"],
        answer=result["answer"],
        total_sources=result["total_sources"],
        sources=sources,
        llm_provider=result["llm_provider"],
        execution_time_seconds=result["execution_time_seconds"]
    )
