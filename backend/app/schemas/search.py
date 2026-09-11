from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query string", min_length=2)
    top_k: int = Field(5, ge=1, le=50, description="Maximum number of relevant chunks to retrieve")
    paper_id: Optional[str] = Field(None, description="Optional paper ID to filter search within a single paper")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score cutoff threshold")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is LangChain and LLM applications?",
                "top_k": 5
            }
        }
    )


class VectorSearchResultItem(BaseModel):
    chunk_id: str
    paper_id: str
    page_number: int
    section_name: str
    text: str
    similarity_score: float

    model_config = ConfigDict(from_attributes=True)


class VectorSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[VectorSearchResultItem]


class EmbeddingJobResponse(BaseModel):
    paper_id: str
    chunks_embedded: int
    status: str = "COMPLETED"
    message: str


class GraphSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query string", min_length=2)
    paper_id: Optional[str] = Field(None, description="Optional paper ID to filter search within a single paper")
    max_depth: int = Field(2, ge=1, le=3, description="Maximum graph traversal hop depth")
    top_k: int = Field(10, ge=1, le=50, description="Maximum number of triples to return")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Which models are evaluated on the GLUE dataset?",
                "top_k": 10,
                "max_depth": 2
            }
        }
    )


class GraphTripleItem(BaseModel):
    source: str = Field(..., description="Source entity canonical name")
    relation_type: str = Field(..., description="Relationship type predicate")
    target: str = Field(..., description="Target entity canonical name")
    description: Optional[str] = Field(None, description="Contextual relationship description")
    paper_id: Optional[str] = Field(None, description="Associated paper ID if applicable")


class ConnectedPaperItem(BaseModel):
    paper_id: str = Field(..., description="Paper unique identifier")
    paper_title: str = Field(..., description="Research paper title")
    matched_entity_count: int = Field(0, description="Number of query entities mentioned by this paper")


class GraphSearchResponse(BaseModel):
    query: str
    matched_entities: List[str] = Field(default_factory=list)
    total_triples: int = 0
    triples: List[GraphTripleItem] = Field(default_factory=list)
    connected_papers: List[ConnectedPaperItem] = Field(default_factory=list)
    formatted_graph_context: str = ""


class HybridSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language query string", min_length=2)
    top_k: int = Field(10, ge=1, le=50, description="Maximum number of hybrid results to retrieve")
    paper_id: Optional[str] = Field(None, description="Optional paper ID filter")
    vector_weight: float = Field(1.0, ge=0.0, le=5.0, description="Weight multiplier for vector search rank")
    graph_weight: float = Field(1.0, ge=0.0, le=5.0, description="Weight multiplier for graph search rank")
    rrf_k: int = Field(60, ge=1, le=100, description="RRF smoothing constant k")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "How is BERT evaluated on GLUE benchmark?",
                "top_k": 10,
                "vector_weight": 1.0,
                "graph_weight": 1.0
            }
        }
    )


class HybridSearchResultItem(BaseModel):
    item_id: str = Field(..., description="Unique identifier (chunk_id or relationship key)")
    item_type: str = Field(..., description="Type of evidence: 'vector_chunk' or 'graph_triple'")
    content: str = Field(..., description="Passage text or relationship triple content")
    paper_id: Optional[str] = Field(None, description="Associated paper ID")
    vector_rank: Optional[int] = Field(None, description="1-based rank in vector search results")
    graph_rank: Optional[int] = Field(None, description="1-based rank in graph search results")
    rrf_score: float = Field(..., description="Calculated Reciprocal Rank Fusion score")
    metadata: dict = Field(default_factory=dict, description="Additional item metadata (page number, section name, relation type, etc.)")


class HybridSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[HybridSearchResultItem]
    matched_graph_entities: List[str] = Field(default_factory=list)
    unified_hybrid_context: str = Field("", description="Unified formatted context combining text chunks and graph triples for LLM prompt ingestion")


