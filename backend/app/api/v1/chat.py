from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.rag.chat_service import GroundedChatService
from app.schemas.rag import ChatRequest, ChatResponse

router = APIRouter(tags=["Grounded Chat Engine"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Grounded Research Q&A Chat Endpoint",
    description="Generates an evidence-grounded research answer using hybrid, vector, or graph retrieval, featuring strict citation tags and hallucination guardrails."
)
async def generate_grounded_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    return await GroundedChatService.generate_grounded_chat(
        db=db,
        request=request
    )
