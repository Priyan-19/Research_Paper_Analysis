import pytest
from app.rag.citation_guard import CitationGuard
from app.schemas.rag import CitationBadge


class TestCitationGuard:
    """Unit tests for CitationGuard extraction, grounding checks, and ID replacement."""

    def test_extract_citation_badges_paper_page_format(self):
        """Extracts badges from [Paper: <id>, Page: <page>] format."""
        text = "Transformers are evaluated on GLUE [Paper: paper_001, Page: 5]."
        sources = [{
            "paper_id": "paper_001",
            "paper_title": "Attention Paper",
            "page_number": 5,
            "section_name": "Experiments",
            "text": "GLUE evaluation results"
        }]

        badges = CitationGuard.extract_citation_badges(text, sources)
        assert len(badges) == 1
        assert badges[0].paper_id == "paper_001"
        assert badges[0].paper_title == "Attention Paper"
        assert badges[0].page_number == 5
        assert badges[0].citation_tag == "[Paper: paper_001, Page: 5]"

    def test_extract_citation_badges_source_idx_format(self):
        """Extracts badges from [Source N] format."""
        text = "According to previous work [Source 1], BERT outperforms earlier baselines."
        sources = [{
            "source_index": 1,
            "paper_id": "p_bert",
            "paper_title": "BERT Study",
            "page_number": 3,
            "text": "BERT outperforms..."
        }]

        badges = CitationGuard.extract_citation_badges(text, sources)
        assert len(badges) == 1
        assert badges[0].paper_id == "p_bert"
        assert badges[0].paper_title == "BERT Study"
        assert badges[0].citation_tag == "[Source 1]"

    def test_extract_badges_empty_or_none(self):
        """Returns empty list when input text or sources are empty."""
        assert CitationGuard.extract_citation_badges("", [{"paper_id": "p1"}]) == []
        assert CitationGuard.extract_citation_badges("Some text without sources", []) == []

    def test_is_insufficient_evidence_checks(self):
        """Identifies empty sources or explicit refusal phrases."""
        # No evidence items retrieved
        assert CitationGuard.is_insufficient_evidence("Answer", []) is True

        # LLM explicitly refuses due to lack of evidence
        refusal = "Based on available texts, there is insufficient evidence to answer this question."
        assert CitationGuard.is_insufficient_evidence(refusal, [{"paper_id": "p1"}]) is True

        # Grounded answer with evidence
        valid_answer = "BERT is a deep bidirectional transformer model [Paper: p1, Page: 1]."
        assert CitationGuard.is_insufficient_evidence(valid_answer, [{"paper_id": "p1"}]) is False

    def test_replace_paper_ids_with_titles(self):
        """Replaces raw UUID IDs in answer text with human-readable titles."""
        raw_uuid = "bdb7a170-b3b0-49dd-be3e-d1d4bf61b27e"
        text = f"Transformer architecture introduced in [Paper: {raw_uuid}, Page: 2]."
        sources = [{
            "paper_id": raw_uuid,
            "paper_title": "Attention Is All You Need"
        }]

        clean_text = CitationGuard.replace_paper_ids_with_titles(text, sources)
        assert raw_uuid not in clean_text
        assert "Attention Is All You Need" in clean_text

