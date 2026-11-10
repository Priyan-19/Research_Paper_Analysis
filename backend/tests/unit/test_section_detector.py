import pytest
from app.ingestion.section_detector import SectionDetector


class TestSectionDetector:
    """Unit tests for academic research paper section header detection."""

    @pytest.mark.parametrize("line,expected_section", [
        ("Abstract", "Abstract"),
        ("1. Abstract", "Abstract"),
        ("1. Introduction", "Introduction"),
        ("Introduction", "Introduction"),
        ("2. Related Work", "Related Work"),
        ("Literature Review", "Related Work"),
        ("3. Methodology", "Methodology"),
        ("Proposed Method", "Methodology"),
        ("Architecture", "Methodology"),
        ("Approach", "Methodology"),
        ("4. Experiments", "Results"),
        ("Experimental Setup", "Results"),
        ("Evaluation", "Results"),
        ("Results", "Results"),
        ("5. Discussion", "Conclusion"),
        ("Conclusion", "Conclusion"),
        ("Future Work", "Conclusion"),
        ("References", "References"),
        ("Bibliography", "References"),
    ])
    def test_detect_known_sections(self, line, expected_section):
        """Matches standard academic section titles with and without numbering."""
        assert SectionDetector.detect_section_name(line) == expected_section

    def test_detect_case_insensitive(self):
        """Ensures detection handles varied casings and whitespace."""
        assert SectionDetector.detect_section_name("   iNtRoDuCtIoN   ") == "Introduction"
        assert SectionDetector.detect_section_name("  2. rElAtEd wOrK ") == "Related Work"

    def test_ignore_long_lines(self):
        """Header lines longer than 80 chars should not be classified as section headings."""
        long_line = "This is a very long introductory sentence that discusses the introduction to neural networks " * 2
        assert SectionDetector.detect_section_name(long_line) is None

    def test_unrelated_line_returns_none(self):
        """Regular paragraphs should return None."""
        assert SectionDetector.detect_section_name("We train the model using Adam optimizer with beta=0.9.") is None

