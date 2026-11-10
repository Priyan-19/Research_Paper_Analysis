import pytest
from app.ingestion.pdf_loader import PDFLoader, PageContent
from app.core.exceptions import PDFProcessingError


class TestPDFLoader:
    """Unit tests for PyMuPDF PDF parsing, handling corrupted and empty documents."""

    def test_extract_pages_valid_pdf(self, sample_pdf_path):
        """Extracts text pages cleanly from a valid academic PDF."""
        pages = PDFLoader.extract_pages(sample_pdf_path)
        assert len(pages) == 2
        assert pages[0].page_number == 1
        assert "Attention Is All You Need" in pages[0].text
        assert "Abstract" in pages[0].text
        assert pages[1].page_number == 2
        assert "Model Architecture" in pages[1].text
        assert "References" in pages[1].text

    def test_extract_pages_non_existent_file(self):
        """Raises PDFProcessingError when the file does not exist on disk."""
        with pytest.raises(PDFProcessingError) as exc_info:
            PDFLoader.extract_pages("non_existent_file_xyz123.pdf")
        assert "File not found" in str(exc_info.value)

    def test_extract_pages_empty_pdf(self, empty_pdf_path):
        """Raises PDFProcessingError when PDF contains no text."""
        with pytest.raises(PDFProcessingError) as exc_info:
            PDFLoader.extract_pages(empty_pdf_path)
        assert "no readable text" in str(exc_info.value)

    def test_extract_pages_corrupted_pdf(self, corrupt_pdf_path):
        """Raises PDFProcessingError on corrupted file bytes."""
        with pytest.raises(PDFProcessingError):
            PDFLoader.extract_pages(corrupt_pdf_path)

    def test_page_content_dataclass(self):
        """Verifies PageContent instantiation and attributes."""
        pc = PageContent(page_number=5, text="Sample text content")
        assert pc.page_number == 5
        assert pc.text == "Sample text content"
