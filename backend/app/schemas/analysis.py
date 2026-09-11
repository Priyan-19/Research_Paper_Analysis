from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class CitationRecommendRequest(BaseModel):
    statement: str = Field(..., description="Draft research claim, paragraph, or statement text to cite for", min_length=5)
    top_k: int = Field(5, ge=1, le=20, description="Maximum number of paper citation recommendations to return")
    exclude_paper_id: Optional[str] = Field(None, description="Optional paper ID to exclude from recommendations")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "statement": "Self-attention mechanisms capture long-range dependencies without recurrent connections.",
                "top_k": 5
            }
        }
    )


class RecommendedCitationItem(BaseModel):
    paper_id: str = Field(..., description="Unique paper identifier")
    paper_title: str = Field(..., description="Title of recommended paper")
    vector_similarity: float = Field(..., description="Cosine similarity score with statement embedding")
    concept_overlap_score: float = Field(..., description="Knowledge Graph entity overlap score")
    overall_score: float = Field(..., description="Combined weighted citation relevance score")
    justification: str = Field(..., description="Generated reasoning explaining why this paper should be cited")
    relevant_snippet: str = Field(..., description="Matching text passage snippet from the paper")

    model_config = ConfigDict(from_attributes=True)


class CitationRecommendResponse(BaseModel):
    statement: str
    total_recommendations: int
    recommendations: List[RecommendedCitationItem]


class PaperSimilarityRequest(BaseModel):
    source_paper_id: str = Field(..., description="Source paper ID to compare")
    target_paper_id: Optional[str] = Field(None, description="Optional target paper ID for pairwise comparison; if omitted, checks against library")
    top_k: int = Field(5, ge=1, le=20, description="Maximum number of similar papers to return")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_paper_id": "paper_001",
                "top_k": 5
            }
        }
    )


class SharedEntityBreakdown(BaseModel):
    shared_concepts: List[str] = Field(default_factory=list)
    shared_methods: List[str] = Field(default_factory=list)
    shared_datasets: List[str] = Field(default_factory=list)
    shared_models: List[str] = Field(default_factory=list)


class PaperSimilarityItem(BaseModel):
    paper_id: str = Field(..., description="Target paper ID")
    paper_title: str = Field(..., description="Target paper title")
    overall_similarity_score: float = Field(..., description="Multi-factor weighted overall similarity score (0.0 to 1.0)")
    vector_similarity: float = Field(..., description="Dense vector embedding similarity score")
    concept_overlap: float = Field(..., description="Knowledge Graph concept overlap ratio")
    method_overlap: float = Field(..., description="Knowledge Graph method/model overlap ratio")
    dataset_overlap: float = Field(..., description="Knowledge Graph dataset overlap ratio")
    classification_label: str = Field(..., description="Objective classification label ('Highly Similar Research', 'Moderately Overlapping', 'Low Overlap')")
    shared_entities: SharedEntityBreakdown = Field(default_factory=SharedEntityBreakdown)

    model_config = ConfigDict(from_attributes=True)


class PaperSimilarityResponse(BaseModel):
    source_paper_id: str
    source_paper_title: str
    total_matches: int
    matches: List[PaperSimilarityItem]


class TrendOverviewResponse(BaseModel):
    total_papers: int = Field(..., description="Total papers indexed in PostgreSQL")
    total_concepts: int = Field(..., description="Total entity nodes in Knowledge Graph")
    total_relationships: int = Field(..., description="Total directed relationships in Knowledge Graph")
    top_concepts: List[Dict[str, Any]] = Field(default_factory=list, description="Top 10 most frequent research concepts")
    publication_year_distribution: Dict[str, int] = Field(default_factory=dict, description="Paper distribution across publication years")


class ConceptTimelineItem(BaseModel):
    concept_name: str = Field(..., description="Canonical entity name")
    entity_type: str = Field(..., description="Entity classification type")
    yearly_counts: Dict[str, int] = Field(default_factory=dict, description="Mentions count grouped by publication year")
    growth_rate: float = Field(0.0, description="Latest year-over-year growth rate Delta")
    is_emerging: bool = Field(False, description="True if growth rate Delta >= 0.50 and recent count >= 2")


class ConceptCoOccurrenceItem(BaseModel):
    concept1: str = Field(..., description="First concept name")
    concept2: str = Field(..., description="Second concept name")
    co_occurrence_count: int = Field(..., description="Number of papers where both concepts co-occur")


class ResearchTrendsResponse(BaseModel):
    timeline: List[ConceptTimelineItem] = Field(default_factory=list)
    emerging_concepts: List[str] = Field(default_factory=list)
    top_co_occurrences: List[ConceptCoOccurrenceItem] = Field(default_factory=list)


