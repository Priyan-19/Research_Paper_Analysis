import pytest
from app.evaluation.metrics import EvaluationMetricsEngine


class TestClaimVerification:
    """Unit tests for Phase 6 Claim-Level Verification and Faithfulness Engine."""

    def test_decompose_into_claims_basic(self):
        answer = (
            "The Transformer model uses multi-head self-attention mechanisms. "
            "It was proposed by Vaswani et al. in 2017. "
            "The architecture completely eliminates recurrent and convolutional layers."
        )
        claims = EvaluationMetricsEngine.decompose_into_claims(answer)
        assert len(claims) == 3
        assert any("multi-head self-attention" in c for c in claims)
        assert any("Vaswani" in c for c in claims)
        assert any("eliminates recurrent" in c for c in claims)

    def test_decompose_into_claims_strips_citations_and_disclaimers(self):
        answer = (
            "Transformers achieved 28.4 BLEU on WMT 2014 English-to-German [Paper: Attention.pdf, Page: 5]. "
            "Based on the analyzed context, the learning rate used was 0.0001."
        )
        claims = EvaluationMetricsEngine.decompose_into_claims(answer)
        # The first claim should have the citation stripped
        assert len(claims) >= 1
        assert "[Paper:" not in claims[0]
        assert "28.4 BLEU" in claims[0]
        # The meta-disclaimer sentence should be filtered out by skip_phrases
        assert not any("based on the analyzed" in c.lower() for c in claims)

    def test_verify_claims_supported(self):
        context = (
            "We propose the Transformer, a model architecture eschewing recurrence and instead "
            "relying entirely on an attention mechanism to draw global dependencies between input and output. "
            "The Transformer allows for significantly more parallelization and reached 28.4 BLEU on WMT 2014."
        )
        answer = "The Transformer relies entirely on an attention mechanism and achieves 28.4 BLEU on WMT 2014."
        result = EvaluationMetricsEngine.verify_claims_against_context(answer, context)

        assert result["total_claims"] == 1
        assert result["supported_count"] == 1
        assert result["unsupported_count"] == 0
        assert result["faithfulness_score"] == 1.0
        assert result["claims"][0]["status"] == "SUPPORTED"

    def test_verify_claims_unsupported_hallucination(self):
        context = "The Transformer relies entirely on an attention mechanism without recurrence."
        answer = "The Transformer was trained using reinforcement learning with human feedback and quantum annealing."
        result = EvaluationMetricsEngine.verify_claims_against_context(answer, context)

        assert result["total_claims"] == 1
        assert result["unsupported_count"] == 1
        assert result["faithfulness_score"] == 0.0
        assert result["claims"][0]["status"] == "UNSUPPORTED"
        assert "not adequately grounded" in result["claims"][0]["explanation"]

    def test_verify_claims_partial_grounding(self):
        context = "The Transformer architecture relies entirely on multi-head attention mechanisms."
        answer = (
            "The Transformer architecture relies entirely on multi-head attention mechanisms. "
            "The model was deployed directly onto superconducting quantum computers in Antarctica."
        )
        result = EvaluationMetricsEngine.verify_claims_against_context(answer, context)

        assert result["total_claims"] == 2
        assert result["supported_count"] == 1
        assert result["unsupported_count"] == 1
        assert result["faithfulness_score"] == 0.5

    def test_insufficient_evidence_response(self):
        answer = "Insufficient evidence found in the retrieved documents to answer this question."
        context = "Some random text."
        result = EvaluationMetricsEngine.verify_claims_against_context(answer, context)

        assert result["faithfulness_score"] == 1.0
        assert result["total_claims"] == 0

    def test_empty_context_marks_all_claims_unsupported(self):
        answer = "BERT is a bidirectional encoder representation trained on masked language modeling."
        result = EvaluationMetricsEngine.verify_claims_against_context(answer, "")

        assert result["total_claims"] == 1
        assert result["unsupported_count"] == 1
        assert result["faithfulness_score"] == 0.0
        assert result["claims"][0]["status"] == "UNSUPPORTED"
        assert "Zero context" in result["claims"][0]["explanation"]

    def test_compute_faithfulness_wrapper(self):
        context = "ResNet introduces residual connections to address degradation in deep neural networks."
        answer = "ResNet introduces residual connections for deep networks."
        score = EvaluationMetricsEngine.compute_faithfulness(answer, context)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score == 1.0

