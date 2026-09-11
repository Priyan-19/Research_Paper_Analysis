import re


class TextCleaner:
    """
    Cleans raw text extracted from PDFs:
    - Removes hyphenated line breaks (e.g., 'trans-\nformer' -> 'transformer')
    - Normalizes multi-spaces and newlines
    - Strips non-printable ASCII noise
    """
    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""

        # 1. Join hyphenated words split across lines: "word-\nnext" -> "wordnext"
        cleaned = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

        # 2. Convert single line breaks within sentences to spaces
        cleaned = re.sub(r'(?<!\n)\n(?!\n)', ' ', cleaned)

        # 3. Normalize multiple blank lines to double newlines
        cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)

        # 4. Collapse multiple horizontal spaces/tabs
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)

        # 5. Remove unusual non-printable control characters
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', cleaned)

        return cleaned.strip()
