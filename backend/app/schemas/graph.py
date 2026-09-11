from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class EntityType(str, Enum):
    CONCEPT = "CONCEPT"
    METHOD = "METHOD"
    DATASET = "DATASET"
    METRIC = "METRIC"
    AUTHOR = "AUTHOR"
    TASK = "TASK"
    MODEL = "MODEL"
    TOOL = "TOOL"


class RelationType(str, Enum):
    USES_METHOD = "USES_METHOD"
    EVALUATED_ON = "EVALUATED_ON"
    PROPOSES = "PROPOSES"
    APPLIES_TO = "APPLIES_TO"
    AUTHORED_BY = "AUTHORED_BY"
    ACHIEVES_METRIC = "ACHIEVES_METRIC"
    EXTENDS = "EXTENDS"


class GraphEntity(BaseModel):
    name: str = Field(..., description="Canonical entity name")
    type: EntityType = Field(..., description="Entity classification type")
    description: Optional[str] = Field(None, description="Short contextual definition or summary")


class GraphRelationship(BaseModel):
    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")
    relation_type: RelationType = Field(..., description="Directed relationship predicate type")
    description: Optional[str] = Field(None, description="Brief explanation of the relationship")


class KnowledgeGraphExtractionResult(BaseModel):
    entities: List[GraphEntity] = Field(default_factory=list)
    relationships: List[GraphRelationship] = Field(default_factory=list)


class GraphNodeResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None


class GraphEdgeResponse(BaseModel):
    source: str
    target: str
    relation_type: str
    description: Optional[str] = None


class PaperGraphResponse(BaseModel):
    paper_id: str
    paper_title: str
    total_nodes: int
    total_edges: int
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]


class GraphStatsResponse(BaseModel):
    total_nodes: int
    total_relationships: int
    entity_type_counts: Dict[str, int]
    relationship_type_counts: Dict[str, int]


class GNNPredictLinksRequest(BaseModel):
    source_entity: str = Field(..., description="Source entity to predict links for")
    target_candidates: List[str] = Field(..., min_length=1, description="List of candidate target entities")
    existing_relationships: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="Optional graph context list of {'source': ..., 'target': ..., 'relation': ...}"
    )
    top_k: int = Field(5, ge=1, le=20, description="Top K link predictions to return")


class GNNLinkPredictionItem(BaseModel):
    target_entity: str = Field(..., description="Candidate target entity name")
    link_probability: float = Field(..., description="Predicted link probability (0-1)")
    similarity_score: float = Field(..., description="Cosine similarity in GNN embedding space")
    gnn_recommendation: str = Field(..., description="Qualitative link recommendation level")


class GNNPredictLinksResponse(BaseModel):
    source_entity: str = Field(..., description="Source entity name")
    total_candidates_evaluated: int = Field(..., description="Total target candidates evaluated")
    predicted_links: List[GNNLinkPredictionItem] = Field(..., description="Ranked predicted link results")
