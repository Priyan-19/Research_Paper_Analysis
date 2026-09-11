from typing import List, Dict, Any
from app.ingestion.pdf_loader import PageContent
from app.ingestion.text_cleaner import TextCleaner
from app.ingestion.section_detector import SectionDetector


class ChunkData:
    def __init__(
        self,
        chunk_index: int,
        page_number: int,
        section_name: str,
        text: str,
        char_length: int,
        token_count: int
    ):
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.section_name = section_name
        self.text = text
        self.char_length = char_length
        self.token_count = token_count


class SemanticChunker:
    """
    Recursive semantic chunker preserving page and section metadata.
    Splits text into chunks (~500-1000 characters) with overlap.
    """
    def __init__(self, target_chunk_size: int = 700, chunk_overlap: int = 100):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(self, pages: List[PageContent]) -> List[ChunkData]:
        chunks: List[ChunkData] = []
        global_chunk_idx = 0
        current_section = "General"

        for page in pages:
            cleaned_text = TextCleaner.clean(page.text)
            lines = cleaned_text.split('\n')

            page_buffer = ""
            for line in lines:
                detected_section = SectionDetector.detect_section_name(line)
                if detected_section:
                    current_section = detected_section

                page_buffer += line + " "

            # Chunk the page_buffer text
            words = page_buffer.split()
            current_chunk_words: List[str] = []
            current_len = 0

            for word in words:
                current_chunk_words.append(word)
                current_len += len(word) + 1

                if current_len >= self.target_chunk_size:
                    chunk_text = " ".join(current_chunk_words).strip()
                    if chunk_text:
                        chunks.append(
                            ChunkData(
                                chunk_index=global_chunk_idx,
                                page_number=page.page_number,
                                section_name=current_section,
                                text=chunk_text,
                                char_length=len(chunk_text),
                                token_count=len(chunk_text.split())
                            )
                        )
                        global_chunk_idx += 1

                    # Keep overlap words
                    overlap_word_count = max(1, int(len(current_chunk_words) * (self.chunk_overlap / self.target_chunk_size)))
                    current_chunk_words = current_chunk_words[-overlap_word_count:]
                    current_len = sum(len(w) + 1 for w in current_chunk_words)

            # Leftover buffer for the page
            if current_chunk_words:
                remainder_text = " ".join(current_chunk_words).strip()
                if len(remainder_text) > 30:  # Only add meaningful remainders
                    chunks.append(
                        ChunkData(
                            chunk_index=global_chunk_idx,
                            page_number=page.page_number,
                            section_name=current_section,
                            text=remainder_text,
                            char_length=len(remainder_text),
                            token_count=len(remainder_text.split())
                        )
                    )
                    global_chunk_idx += 1

        return chunks
