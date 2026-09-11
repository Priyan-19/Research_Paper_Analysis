import re
from typing import List, Dict, Any, Optional, Set


class EvaluationMetricsEngine:
    """
    Automated RAGAS-compatible Evaluation Metrics Engine.
    Computes Faithfulness, Context Precision, Context Recall, Answer Relevance, and MRR.
    """

    @classmethod
    def compute_faithfulness(cls, answer: str, context: str) -> float:
        """
        Calculates Faithfulness (Evidence Grounding) score in [0.0, 1.0].
        Measures the proportion of statements in answer supported by retrieved context.
        """
        if not answer or not answer.strip():
            return 0.0

        # If answer explicitly acknowledges insufficient evidence when context is missing, faithfulness is 1.0
        insufficient_phrases = ["insufficient evidence", "no evidence found", "not provided in context"]
        if any(phrase in answer.lower() for phrase in insufficient_phrases):
            return 1.0

        if not context or not context.strip():
            # Answer generated content without any context provided -> ungrounded (0.0)
            return 0.0

        # Extract non-trivial words (min length 4) from answer and context
        ans_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', answer.lower()))
        ctx_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', context.lower()))

        if not ans_words:
            return 1.0

        overlap = ans_words.intersection(ctx_words)
        faithfulness_score = min(1.0, len(overlap) / len(ans_words))
        return round(faithfulness_score, 4)

    @classmethod
    def compute_context_precision(
        cls,
        retrieved_entities: List[str],
        target_entities: List[str]
    ) -> float:
        """
        Calculates Context Precision@K score: |Retrieved ∩ Target| / |Retrieved|.
        """
        if not retrieved_entities or not target_entities:
            return 0.0

        ret_set = {e.lower() for e in retrieved_entities}
        tgt_set = {e.lower() for e in target_entities}

        intersection = ret_set.intersection(tgt_set)
        precision = len(intersection) / len(ret_set)
        return round(precision, 4)

    @classmethod
    def compute_context_recall(
        cls,
        retrieved_entities: List[str],
        target_entities: List[str]
    ) -> float:
        """
        Calculates Context Recall score: |Retrieved ∩ Target| / |Target|.
        """
        if not target_entities:
            return 1.0
        if not retrieved_entities:
            return 0.0

        ret_set = {e.lower() for e in retrieved_entities}
        tgt_set = {e.lower() for e in target_entities}

        intersection = ret_set.intersection(tgt_set)
        recall = len(intersection) / len(tgt_set)
        return round(recall, 4)

    @classmethod
    def compute_mrr(
        cls,
        retrieved_entities: List[str],
        target_entities: List[str]
    ) -> float:
        """
        Calculates Mean Reciprocal Rank (MRR): 1 / rank of first relevant entity match.
        """
        if not retrieved_entities or not target_entities:
            return 0.0

        tgt_set = {e.lower() for e in target_entities}
        for rank_idx, ent in enumerate(retrieved_entities, start=1):
            if ent.lower() in tgt_set:
                return round(1.0 / rank_idx, 4)

        return 0.0

    @classmethod
    def compute_answer_relevance(cls, query: str, answer: str) -> float:
        """
        Calculates Answer Relevance score based on semantic term overlap between question and answer.
        """
        if not query or not answer:
            return 0.0

        q_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))
        a_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', answer.lower()))

        stop_words = {"what", "which", "where", "when", "how", "why", "this", "that", "does", "have"}
        q_words = q_words - stop_words

        if not q_words:
            return 0.5

        overlap = q_words.intersection(a_words)
        relevance = len(overlap) / len(q_words)
        return round(min(1.0, relevance + 0.3), 4)  # Normalize with base relevance factor
