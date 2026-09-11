import re
from typing import Optional


class SectionDetector:
    """
    Detects standard academic research paper sections from text lines.
    """
    SECTION_PATTERNS = [
        (r'^\s*(?:1\.?\s*)?abstract\b', "Abstract"),
        (r'^\s*(?:1\.?\s*)?introduction\b', "Introduction"),
        (r'^\s*(?:2\.?\s*)?(?:related\s+work|literature\s+review)\b', "Related Work"),
        (r'^\s*(?:\d+\.?\s*)?(?:methodology|proposed\s+method|method|architecture|approach)\b', "Methodology"),
        (r'^\s*(?:\d+\.?\s*)?(?:experiments|experimental\s+setup|evaluation|results)\b', "Results"),
        (r'^\s*(?:\d+\.?\s*)?(?:discussion|conclusion|future\s+work)\b', "Conclusion"),
        (r'^\s*(?:\d+\.?\s*)?(?:references|bibliography)\b', "References"),
    ]

    @classmethod
    def detect_section_name(cls, line: str) -> Optional[str]:
        """
        Checks if a text line matches a known section header pattern.
        """
        clean_line = line.strip().lower()
        if len(clean_line) > 80:  # Headers are usually short
            return None

        for pattern, section_title in cls.SECTION_PATTERNS:
            if re.match(pattern, clean_line, re.IGNORECASE):
                return section_title

        return None
