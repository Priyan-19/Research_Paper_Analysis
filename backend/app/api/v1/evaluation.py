import os
import json
from fastapi import APIRouter, status, HTTPException

from app.schemas.evaluation import EvaluationReportResponse
from scripts.evaluate_rag import RAGAblationEvaluator

router = APIRouter(prefix="/evaluation", tags=["Evaluation Benchmark Engine"])

RESULTS_FILE = os.path.join("data", "evaluation", "benchmark_results.json")


@router.get(
    "/results",
    response_model=EvaluationReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Quantitative RAG Benchmark Results",
    description="Retrieves quantitative ablation study results comparing LLM-Only, Vector RAG, Graph RAG, and Hybrid RAG across Faithfulness, Precision, Recall, and MRR metrics."
)
async def get_evaluation_results():
    if not os.path.exists(RESULTS_FILE):
        # Run ablation evaluation on-the-fly if report file does not exist
        return await RAGAblationEvaluator.run_ablation_evaluation()


    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return EvaluationReportResponse(**data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read evaluation benchmark results: {str(e)}"
        )
