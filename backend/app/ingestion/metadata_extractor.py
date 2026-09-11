import re
from typing import Dict, Any, List, Optional
from app.ingestion.pdf_loader import PageContent


class MetadataExtractor:
    """
    Extracts paper metadata (Title, Authors, Abstract, Year) from PDF text content.
    Filters out journal headers, DOIs, URLs, and publisher watermarks to locate the true paper title.
    """

    HEADER_SKIP_PATTERNS = [
        r'international journal', r'journal of', r'ijrcait', r'ieee', r'acm', r'arxiv:', r'volume \d+',
        r'issue \d+', r'available online', r'https?://', r'www\.', r'doi:', r'issn', r'isbn',
        r'article id:', r'\bpp\.', r'copyright', r'all rights reserved', r'open access',
        r'publication', r'proceeding', r'conference on', r'iaeme'
    ]

    AFFILIATION_PATTERNS = r'(@|university|department|engineer|paypal|google|meta|microsoft|author|\bby\b|brain|research|lab|institute|faculty|school|college|inc\.|corp)'

    @classmethod
    def extract_metadata(cls, pages: List[PageContent], filename: str) -> Dict[str, Any]:
        clean_filename_title = filename.replace(".pdf", "").replace("_", " ").replace("-", " ").title()

        if not pages:
            return {
                "title": clean_filename_title,
                "authors": [],
                "abstract": "",
                "publication_year": None
            }

        first_page_text = pages[0].text
        lines = [line.strip() for line in first_page_text.split('\n') if line.strip()]

        # 1. Filter out journal headers & publisher metadata lines
        candidate_lines = []
        for line in lines:
            if any(re.search(pat, line.lower()) for pat in cls.HEADER_SKIP_PATTERNS):
                continue
            candidate_lines.append(line)

        # 2. Extract Title
        title_parts = []
        abstract_start_idx = len(candidate_lines)

        for idx, line in enumerate(candidate_lines):
            # Stop if we reach ABSTRACT, KEYWORDS, or Section 1
            if re.search(r'^(abstract|keywords|1\.\s*introduction)\b', line.lower()):
                abstract_start_idx = idx
                break

            # Stop if current line matches affiliation keywords
            if re.search(cls.AFFILIATION_PATTERNS, line.lower()):
                break

            # If title_parts exists and next line is affiliation, stop before author name
            if title_parts and idx < len(candidate_lines) - 1:
                next_l = candidate_lines[idx + 1].lower()
                if re.search(cls.AFFILIATION_PATTERNS, next_l):
                    break

            title_parts.append(line)
            if len(title_parts) >= 3:
                break

        title = " ".join(title_parts).strip() if title_parts else ""

        # Fallback to cleaned filename title if extracted title is invalid/short/URL
        if not title or len(title) < 5 or re.search(r'^https?://', title.lower()):
            title = clean_filename_title
        elif len(title) > 250:
            title = title[:250] + "..."

        # Normalize ALL CAPS titles to Title Case
        if title.isupper() and len(title) > 10:
            title = title.title()

        # 3. Extract Abstract
        abstract = ""
        full_text = "\n".join([p.text for p in pages[:2]])
        abstract_match = re.search(r'abstract[:\s\n]+(.*?)(?=\n\s*(?:1\.?\s*)?introduction|\n\s*(?:2\.?\s*)?keywords|\n\s*\n\s*\n)', full_text, re.DOTALL | re.IGNORECASE)
        if abstract_match:
            abstract = abstract_match.group(1).replace('\n', ' ').strip()
            if len(abstract) > 2000:
                abstract = abstract[:2000]

        # 4. Extract Publication Year
        publication_year = None
        year_match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', first_page_text)
        if year_match:
            publication_year = int(year_match.group(1))

        # 5. Extract Authors
        authors: List[str] = []
        author_search_lines = candidate_lines[len(title_parts):abstract_start_idx]
        for line in author_search_lines:
            if re.search(r'abstract|keywords|introduction|issn|doi', line.lower()):
                continue
            if len(line) < 100 and not line.endswith('.'):
                parts = [a.strip() for a in re.split(r',| and |\*', line) if len(a.strip()) > 2]
                for p in parts:
                    if not re.search(cls.AFFILIATION_PATTERNS, p.lower()):
                        authors.append(p)
            if authors:
                break

        return {
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "publication_year": publication_year
        }
