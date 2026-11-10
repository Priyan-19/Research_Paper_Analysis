from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.rag.chat_service import GroundedChatService
from app.services.paper_service import PaperService
from app.core.security import get_current_user_optional
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
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    user_id = current_user.get("user_id") if current_user else None
    if request.paper_id:
        await PaperService.get_paper_by_id(db, request.paper_id, user_id=user_id)

    return await GroundedChatService.generate_grounded_chat(
        db=db,
        request=request
    )
