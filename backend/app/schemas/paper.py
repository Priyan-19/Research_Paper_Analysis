from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


# --- Chunk Schemas ---

class ChunkBase(BaseModel):
    chunk_index: int
    page_number: int
    section_name: str
    text: str
    char_length: int
    token_count: int


class ChunkResponse(ChunkBase):
    id: str
    paper_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChunkListResponse(BaseModel):
    paper_id: str
    total_chunks: int
    chunks: List[ChunkResponse]


# --- Paper Schemas ---

class PaperBase(BaseModel):
    title: Optional[str] = None
    authors: Optional[List[str]] = Field(default_factory=list)
    abstract: Optional[str] = None
    publication_year: Optional[int] = None


class PaperCreate(PaperBase):
    filename: str
    file_path: str
    file_size_bytes: int


class PaperResponse(PaperBase):
    id: str
    filename: str
    file_size_bytes: int
    total_pages: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaperDetailResponse(PaperResponse):
    total_chunks: int = 0
    chunks: Optional[List[ChunkResponse]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PaperListResponse(BaseModel):
    total: int
    papers: List[PaperResponse]


# --- Processing Job Schemas ---

class ProcessingJobResponse(BaseModel):
    id: str
    paper_id: str
    status: str
    current_step: Optional[str] = None
    progress_percentage: float
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
