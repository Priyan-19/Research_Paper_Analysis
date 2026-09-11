from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class VectorRAGRequest(BaseModel):
    query: str = Field(..., description="Research question to be answered", min_length=2)
    top_k: int = Field(5, ge=1, le=20, description="Number of top relevant passages to retrieve as evidence")
    paper_id: Optional[str] = Field(None, description="Optional paper ID to restrict search within a single paper")
    temperature: float = Field(0.2, ge=0.0, le=1.0, description="LLM sampling temperature for answer generation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What are the main applications and architectural benefits of LangChain?",
                "top_k": 5,
                "temperature": 0.2
            }
        }
    )


class RAGSourceItem(BaseModel):
    source_index: int
    paper_id: str
    paper_title: str
    page_number: int
    section_name: str
    chunk_id: str
    similarity_score: float

    model_config = ConfigDict(from_attributes=True)


class VectorRAGResponse(BaseModel):
    query: str
    answer: str
    total_sources: int
    sources: List[RAGSourceItem]
    llm_provider: str
    execution_time_seconds: float


class SearchModeEnum(str, Enum):
    HYBRID = "hybrid"
    VECTOR = "vector"
    GRAPH = "graph"


class ChatRequest(BaseModel):
    query: str = Field(..., description="Research question to answer", min_length=2)
    search_mode: SearchModeEnum = Field(SearchModeEnum.HYBRID, description="Unified Hybrid RAG retrieval mode (Vector Search + Knowledge Graph RRF)")
    paper_id: Optional[str] = Field(None, description="Optional paper ID to restrict search within a single paper")
    top_k: int = Field(10, ge=1, le=50, description="Maximum evidence items to retrieve")
    temperature: float = Field(0.2, ge=0.0, le=1.0, description="LLM sampling temperature")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Which models perform best on GLUE according to the research papers?",
                "search_mode": "hybrid",
                "top_k": 10,
                "temperature": 0.2
            }
        }
    )


class CitationBadge(BaseModel):
    paper_id: str = Field(..., description="Paper unique identifier")
    paper_title: str = Field(..., description="Research paper title")
    page_number: Optional[int] = Field(None, description="Page number where claim is sourced")
    section_name: Optional[str] = Field(None, description="Paper section name")
    citation_tag: str = Field(..., description="Inline citation tag string in generated text")
    snippet: Optional[str] = Field(None, description="Relevant source snippet")

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    query: str
    answer: str
    search_mode: str
    total_citations: int = 0
    citations: List[CitationBadge] = Field(default_factory=list)
    insufficient_evidence: bool = False
    llm_provider: str
    execution_time_seconds: float

