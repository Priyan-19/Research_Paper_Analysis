from typing import List, Dict, Any, Tuple
from app.embeddings.vector_store import VectorSearchResult


class FormattedContext:
    def __init__(self, context_text: str, sources_metadata: List[Dict[str, Any]]):
        self.context_text = context_text
        self.sources_metadata = sources_metadata


class ContextBuilder:
    """
    Assembles retrieved text chunks into structured context blocks for LLM consumption.
    """
    @staticmethod
    def build_vector_context(
        search_results: List[VectorSearchResult],
        paper_titles: Dict[str, str]
    ) -> FormattedContext:
        """
        Formats top-K vector search results into numbered context passages with source metadata.
        """
        if not search_results:
            return FormattedContext(
                context_text="[No relevant document context found.]",
                sources_metadata=[]
            )

        context_blocks = []
        sources_meta = []

        for idx, result in enumerate(search_results, start=1):
            title = paper_titles.get(result.paper_id, "Unknown Paper")
            
            block = (
                f"[Source {idx}]\n"
                f"Paper: {title} (ID: {result.paper_id})\n"
                f"Location: Page {result.page_number} | Section: {result.section_name}\n"
                f"Similarity Score: {result.similarity_score}\n"
                f"Passage: {result.text}\n"
            )
            context_blocks.append(block)

            sources_meta.append({
                "source_index": idx,
                "chunk_id": result.chunk_id,
                "paper_id": result.paper_id,
                "paper_title": title,
                "page_number": result.page_number,
                "section_name": result.section_name,
                "similarity_score": result.similarity_score
            })

        full_context = "\n---\n".join(context_blocks)
        return FormattedContext(context_text=full_context, sources_metadata=sources_meta)
