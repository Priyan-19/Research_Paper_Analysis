from pathlib import Path
from typing import List, Dict, Any
import pymupdf as fitz  # PyMuPDF

from app.core.exceptions import PDFProcessingError
from app.core.logging import logger


class PageContent:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text


class PDFLoader:
    """
    Layout-aware PDF loader using PyMuPDF (fitz).
    Extracts structured page content and basic document properties.
    """
    @staticmethod
    def extract_pages(file_path: str) -> List[PageContent]:
        """
        Reads a PDF file and extracts text for each page cleanly.
        """
        path = Path(file_path)
        if not path.exists():
            raise PDFProcessingError(filename=path.name, reason="File not found on disk.")

        try:
            doc = fitz.open(file_path)
            pages: List[PageContent] = []

            for page_idx in range(len(doc)):
                page = doc[page_idx]
                text = page.get_text("text")  # Layout-oriented text extraction
                
                if text and text.strip():
                    pages.append(PageContent(page_number=page_idx + 1, text=text.strip()))

            doc.close()
            
            if not pages:
                raise PDFProcessingError(filename=path.name, reason="PDF contains no readable text or is scanned image without OCR.")

            logger.info(f"Successfully extracted {len(pages)} pages from {path.name}")
            return pages

        except Exception as e:
            if isinstance(e, PDFProcessingError):
                raise e
            logger.error(f"Error reading PDF {path.name}: {str(e)}")
            raise PDFProcessingError(filename=path.name, reason=str(e))
