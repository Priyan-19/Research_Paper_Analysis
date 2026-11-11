from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pymupdf as fitz  # PyMuPDF

from app.core.exceptions import PDFProcessingError
from app.core.logging import logger


class PageContent:
    def __init__(
        self,
        page_number: int,
        text: str,
        tables: Optional[List[Dict[str, Any]]] = None,
        is_ocr: bool = False
    ):
        self.page_number = page_number
        self.text = text
        self.tables = tables or []
        self.has_tables = len(self.tables) > 0
        self.is_ocr = is_ocr


class PDFLoader:
    """
    Layout-aware PDF loader using PyMuPDF (fitz).
    Extracts structured page content, detects and preserves formatted markdown tables,
    and provides an automatic OCR fallback path for scanned or low-text PDF pages.
    """

    @staticmethod
    def extract_tables_from_page(page: fitz.Page, page_number: int) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts structured tables from a PDF page using PyMuPDF TableFinder,
        converting them into markdown tables while preserving column relationships and benchmarks.
        """
        table_markdown_blocks: List[str] = []
        structured_tables: List[Dict[str, Any]] = []

        try:
            tabs = page.find_tables()
            for tab_idx, tab in enumerate(tabs, start=1):
                raw_data = tab.extract()
                if not raw_data or len(raw_data) < 2:
                    continue

                headers = [str(c or "").strip() for c in raw_data[0]]
                rows = [[str(cell or "").strip() for cell in row] for row in raw_data[1:]]

                # Format clean markdown table
                md_header = "| " + " | ".join(headers) + " |"
                md_sep = "| " + " | ".join(["---"] * len(headers)) + " |"
                md_rows = ["| " + " | ".join(row) + " |" for row in rows]
                table_md = f"\n\n[Table {tab_idx} on Page {page_number}]\n" + "\n".join([md_header, md_sep] + md_rows)

                table_markdown_blocks.append(table_md)
                structured_tables.append({
                    "table_index": tab_idx,
                    "page_number": page_number,
                    "headers": headers,
                    "row_count": len(rows),
                    "markdown": table_md
                })
        except Exception as e:
            logger.debug(f"PyMuPDF table extraction skipped for page {page_number}: {str(e)}")

        combined_table_md = "\n".join(table_markdown_blocks)
        return combined_table_md, structured_tables

    @staticmethod
    def attempt_ocr_extraction(page: fitz.Page, page_number: int) -> Optional[str]:
        """
        Attempts OCR extraction on scanned pages with minimal readable digital text.
        Gracefully handles missing OCR binaries without crashing.
        """
        try:
            # PyMuPDF built-in OCR textpage if Tesseract is installed
            textpage_ocr = page.get_textpage_ocr(dpi=150, full=True)
            ocr_text = page.get_text("text", textpage=textpage_ocr)
            if ocr_text and ocr_text.strip():
                logger.info(f"Successfully applied OCR fallback to Page {page_number} ({len(ocr_text)} chars extracted)")
                return ocr_text.strip()
        except Exception as ocr_err:
            logger.debug(f"OCR not available or failed for Page {page_number}: {str(ocr_err)}")

        return None

    @classmethod
    def extract_pages(cls, file_path: str) -> List[PageContent]:
        """
        Reads a PDF file, extracts text, tables, and applies OCR fallback where necessary.
        """
        path = Path(file_path)
        if not path.exists():
            # Try alternate paths (e.g. backend/ relative or current working directory)
            candidates = [
                Path("backend") / file_path,
                Path("..") / file_path,
                Path(__file__).resolve().parent.parent.parent / file_path
            ]
            found = False
            for cand in candidates:
                if cand.exists():
                    path = cand
                    file_path = str(cand)
                    found = True
                    break
            if not found:
                raise PDFProcessingError(filename=path.name, reason="File not found on disk.")

        try:
            doc = fitz.open(file_path)
            pages: List[PageContent] = []

            for page_idx in range(len(doc)):
                page_number = page_idx + 1
                page = doc[page_idx]
                
                # 1. Standard text extraction
                text = page.get_text("text") or ""
                is_ocr_applied = False

                # 2. Check for scanned page (insufficient text < 50 characters)
                if len(text.strip()) < 50:
                    ocr_result = cls.attempt_ocr_extraction(page, page_number)
                    if ocr_result:
                        text = ocr_result
                        is_ocr_applied = True

                # 3. Extract structured tables
                table_md, structured_tables = cls.extract_tables_from_page(page, page_number)
                
                # Append table markdown to page text if tables were found
                if table_md:
                    text = (text.strip() + "\n" + table_md).strip()

                if text and text.strip():
                    pages.append(
                        PageContent(
                            page_number=page_number,
                            text=text.strip(),
                            tables=structured_tables,
                            is_ocr=is_ocr_applied
                        )
                    )

            doc.close()

            if not pages:
                raise PDFProcessingError(
                    filename=path.name,
                    reason="PDF contains no readable text or is scanned image without accessible OCR."
                )

            logger.info(f"Successfully extracted {len(pages)} pages from {path.name} (Tables preserved, OCR enabled)")
            return pages

        except Exception as e:
            if isinstance(e, PDFProcessingError):
                raise e
            logger.error(f"Error reading PDF {path.name}: {str(e)}")
            raise PDFProcessingError(filename=path.name, reason=str(e))
