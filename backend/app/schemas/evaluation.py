from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class BenchmarkResultItem(BaseModel):
    experiment_name: str = Field(..., description="Experiment configuration name (e.g. 'LLM Only', 'Vector RAG', 'Graph RAG', 'Hybrid RAG')")
    faithfulness: float = Field(..., description="Faithfulness / Evidence Grounding score (0.0 to 1.0)")
    context_precision: float = Field(..., description="Context Precision@K score (0.0 to 1.0)")
    context_recall: float = Field(..., description="Context Recall score (0.0 to 1.0)")
    answer_relevance: float = Field(..., description="Semantic Answer Relevance score (0.0 to 1.0)")
    mrr: float = Field(..., description="Mean Reciprocal Rank (MRR)")
    avg_execution_time_seconds: float = Field(..., description="Average latency per question in seconds")

    model_config = ConfigDict(from_attributes=True)


class EvaluationReportResponse(BaseModel):
    timestamp: str = Field(..., description="Benchmark execution ISO timestamp")
    total_questions: int = Field(..., description="Number of evaluation questions evaluated")
    winning_strategy: str = Field(..., description="Strategy with highest overall benchmark score")
    results: List[BenchmarkResultItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
