from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.postgres import get_db
from app.services.paper_service import PaperService
from app.schemas.paper import (
    PaperResponse,
    PaperDetailResponse,
    PaperListResponse,
    ChunkListResponse,
    ChunkResponse
)
from app.core.config import settings

router = APIRouter(prefix="/papers", tags=["Research Papers"])


@router.post(
    "/upload",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Parse Research Paper PDF",
    description="Accepts a PDF research paper, extracts text page-by-page, parses sections, extracts metadata, and generates structured text chunks."
)
async def upload_paper(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # Validate PDF extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files (.pdf) are supported."
        )

    file_bytes = await file.read()
    
    # Validate file size limit
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    paper = await PaperService.process_and_save_paper(
        db=db,
        file_bytes=file_bytes,
        original_filename=file.filename
    )
    return paper


@router.get(
    "",
    response_model=PaperListResponse,
    summary="List All Ingested Research Papers",
    description="Retrieves a paginated list of ingested research papers."
)
async def list_papers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    papers, total = await PaperService.list_papers(db, skip=skip, limit=limit)
    return PaperListResponse(total=total, papers=papers)


@router.get(
    "/{paper_id}",
    response_model=PaperDetailResponse,
    summary="Get Research Paper Details",
    description="Retrieves metadata, processing status, and chunk count for a specific paper."
)
async def get_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    paper = await PaperService.get_paper_by_id(db, paper_id)
    chunks = await PaperService.get_paper_chunks(db, paper_id)
    
    chunk_responses = [ChunkResponse.model_validate(c) for c in chunks]
    return PaperDetailResponse(
        id=paper.id,
        filename=paper.filename,
        file_size_bytes=paper.file_size_bytes,
        total_pages=paper.total_pages,
        status=paper.status,
        error_message=paper.error_message,
        title=paper.title,
        authors=paper.authors or [],
        abstract=paper.abstract,
        publication_year=paper.publication_year,
        created_at=paper.created_at,
        updated_at=paper.updated_at,
        total_chunks=len(chunks),
        chunks=chunk_responses
    )


@router.get(
    "/{paper_id}/chunks",
    response_model=ChunkListResponse,
    summary="Get Extracted Text Chunks for a Paper",
    description="Retrieves all structured text chunks associated with a research paper, including page numbers and section tags."
)
async def get_paper_chunks(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    chunks = await PaperService.get_paper_chunks(db, paper_id)
    return ChunkListResponse(
        paper_id=paper_id,
        total_chunks=len(chunks),
        chunks=[ChunkResponse.model_validate(c) for c in chunks]
    )


@router.delete(
    "/{paper_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Research Paper",
    description="Deletes a research paper record, its parsed chunks, and removes its physical file from disk."
)
async def delete_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    await PaperService.delete_paper(db, paper_id)
    return None
