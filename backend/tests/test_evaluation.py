import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.evaluation.metrics import EvaluationMetricsEngine
from app.schemas.evaluation import EvaluationReportResponse, BenchmarkResultItem
from scripts.evaluate_rag import RAGAblationEvaluator

client = TestClient(app)


def test_evaluation_metrics_engine():
    """
    Tests RAGAS metric formulas for Faithfulness, Precision, Recall, and MRR.
    """
    answer = "BERT is a model evaluated on GLUE dataset."
    context = "BERT model is evaluated on the GLUE benchmark dataset."

    # Test Faithfulness
    f_score = EvaluationMetricsEngine.compute_faithfulness(answer, context)
    assert f_score > 0.5

    # Test Precision & Recall
    retrieved = ["BERT", "GLUE", "PyMuPDF"]
    target = ["BERT", "GLUE"]

    precision = EvaluationMetricsEngine.compute_context_precision(retrieved, target)
    assert precision == pytest.approx(2 / 3, abs=1e-3)

    recall = EvaluationMetricsEngine.compute_context_recall(retrieved, target)
    assert recall == 1.0

    # Test MRR (BERT is at index 1 -> MRR = 1.0)
    mrr = EvaluationMetricsEngine.compute_mrr(retrieved, target)
    assert mrr == 1.0


@pytest.mark.asyncio
async def test_run_ablation_evaluation():
    """
    Tests RAGAblationEvaluator execution across all 4 experiments.
    """
    with patch("app.rag.graph_retriever.GraphRetriever.search_graph", new_callable=AsyncMock) as mock_gsearch:
        mock_gsearch.return_value = MagicMock(
            formatted_graph_context="Graph context evidence",
            matched_entities=["BERT"]
        )

        report = await RAGAblationEvaluator.run_ablation_evaluation()

        assert report.total_questions > 0
        assert len(report.results) == 4
        assert report.winning_strategy != ""


def test_evaluation_results_api_endpoint():
    """
    Tests FastAPI REST endpoint GET /api/v1/evaluation/results.
    """
    with patch("os.path.exists", return_value=False), \
         patch.object(RAGAblationEvaluator, "run_ablation_evaluation", new_callable=AsyncMock) as mock_eval:

        mock_eval.return_value = EvaluationReportResponse(
            timestamp="2026-09-08T18:00:00Z",
            total_questions=4,
            winning_strategy="Experiment D (Hybrid RAG — Proposed)",
            results=[
                BenchmarkResultItem(
                    experiment_name="Experiment D (Hybrid RAG — Proposed)",
                    faithfulness=0.95,
                    context_precision=0.90,
                    context_recall=1.0,
                    answer_relevance=0.92,
                    mrr=1.0,
                    avg_execution_time_seconds=0.15
                )
            ]
        )

        res = client.post if False else client.get("/api/v1/evaluation/results")
        assert res.status_code == 200
        data = res.json()
        assert data["total_questions"] == 4
        assert "Hybrid RAG" in data["winning_strategy"]
        assert len(data["results"]) == 1



if __name__ == "__main__":
    pytest.main(["-v", __file__])
