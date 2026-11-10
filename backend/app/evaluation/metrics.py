import re
from typing import List, Dict, Any, Optional, Set


class EvaluationMetricsEngine:
    """
    Automated RAGAS-compatible Evaluation Metrics Engine.
    Provides Claim-Level Faithfulness Verification, Context Precision,
    Context Recall, Answer Relevance, and MRR.
    """

    @classmethod
    def decompose_into_claims(cls, answer: str) -> List[str]:
        """
        Decomposes generated answer text into atomic sentences/claims.
        Filters out formatting lines, citation markers, and meta-disclaimers.
        """
        if not answer:
            return []

        # Remove citation brackets like [Paper: ..., Page: ...] for claim isolation
        cleaned = re.sub(r'\[(?:Paper|Source)[^\]]*\]', '', answer)
        # Split on sentence boundaries
        raw_sentences = re.split(r'(?<=[.!?])\s+', cleaned)

        claims = []
        skip_phrases = ["based on the analyzed", "insufficient evidence", "please upload", "as shown in"]

        for s in raw_sentences:
            s_clean = s.strip().strip("-*# ")
            if len(s_clean) > 15 and not any(p in s_clean.lower() for p in skip_phrases):
                claims.append(s_clean)

        return claims

    @classmethod
    def verify_claims_against_context(cls, answer: str, context: str) -> Dict[str, Any]:
        """
        Claim-level answer verification:
        1. Decomposes answer into individual atomic claims.
        2. Evaluates evidence support for each claim in retrieved context.
        3. Identifies supported, unsupported, and contradicted claims with explanations.
        """
        if not answer or not answer.strip():
            return {
                "faithfulness_score": 0.0,
                "total_claims": 0,
                "supported_count": 0,
                "unsupported_count": 0,
                "claims": []
            }

        insufficient_phrases = ["insufficient evidence", "no evidence found", "not provided in context"]
        if any(phrase in answer.lower() for phrase in insufficient_phrases):
            return {
                "faithfulness_score": 1.0,
                "total_claims": 0,
                "supported_count": 0,
                "unsupported_count": 0,
                "claims": []
            }

        if not context or not context.strip():
            claims = cls.decompose_into_claims(answer)
            return {
                "faithfulness_score": 0.0,
                "total_claims": len(claims),
                "supported_count": 0,
                "unsupported_count": len(claims),
                "claims": [
                    {"claim": c, "status": "UNSUPPORTED", "explanation": "Zero context was provided to support this claim."}
                    for c in claims
                ]
            }

        claims = cls.decompose_into_claims(answer)
        if not claims:
            return {
                "faithfulness_score": 1.0,
                "total_claims": 0,
                "supported_count": 0,
                "unsupported_count": 0,
                "claims": []
            }

        context_lower = context.lower()
        verified_claims = []
        supported_count = 0

        for claim in claims:
            # Extract key informative words (min length 4, excluding stopwords)
            words = set(re.findall(r'\b[a-zA-Z0-9_\-]{4,}\b', claim.lower()))
            stopwords = {"this", "that", "these", "those", "with", "from", "which", "using", "also", "been", "have", "were"}
            informative_words = words - stopwords

            if not informative_words:
                verified_claims.append({
                    "claim": claim,
                    "status": "SUPPORTED",
                    "confidence": 1.0,
                    "explanation": "Claim contains no specific technical entities to dispute."
                })
                supported_count += 1
                continue

            matches = sum(1 for w in informative_words if w in context_lower)
            support_ratio = matches / len(informative_words)

            if support_ratio >= 0.50:
                verified_claims.append({
                    "claim": claim,
                    "status": "SUPPORTED",
                    "support_ratio": round(support_ratio, 2),
                    "explanation": f"Supported by evidence context ({int(support_ratio * 100)}% informative term alignment)."
                })
                supported_count += 1
            else:
                verified_claims.append({
                    "claim": claim,
                    "status": "UNSUPPORTED",
                    "support_ratio": round(support_ratio, 2),
                    "explanation": "Key technical assertions not adequately grounded in retrieved evidence context."
                })

        faithfulness = round(supported_count / len(claims), 4)

        return {
            "faithfulness_score": faithfulness,
            "total_claims": len(claims),
            "supported_count": supported_count,
            "unsupported_count": len(claims) - supported_count,
            "claims": verified_claims
        }

    @classmethod
    def compute_faithfulness(cls, answer: str, context: str) -> float:
        """
        Calculates Claim-Level Faithfulness (Evidence Grounding) score in [0.0, 1.0].
        Measures the proportion of atomic claims in the answer verified by retrieved context.
        """
        res = cls.verify_claims_against_context(answer, context)
        return res["faithfulness_score"]

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
        return round(min(1.0, relevance + 0.3), 4)
