from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pgvector.sqlalchemy import Vector

from app.core.logging import logger
from app.core.exceptions import ResourceNotFoundError
from app.models.paper import Paper, Chunk
from app.embeddings.embedding_service import get_embedding_service


class VectorSearchResult:
    def __init__(
        self,
        chunk_id: str,
        paper_id: str,
        page_number: int,
        section_name: str,
        text: str,
        similarity_score: float,
        paper_title: Optional[str] = None
    ):
        self.chunk_id = chunk_id
        self.paper_id = paper_id
        self.page_number = page_number
        self.section_name = section_name
        self.text = text
        self.similarity_score = similarity_score
        self.paper_title = paper_title or paper_id


class VectorStoreService:
    """
    Service managing vector embedding generation and pgvector similarity search.
    """
    @staticmethod
    async def embed_paper_chunks(db: AsyncSession, paper_id: str) -> int:
        """
        Fetches all text chunks for a paper, generates vector embeddings, and persists to pgvector.
        Returns count of embedded chunks.
        """
        # Ensure paper exists
        paper_query = select(Paper).where(Paper.id == paper_id)
        paper = (await db.execute(paper_query)).scalar_one_or_none()
        if not paper:
            raise ResourceNotFoundError(resource_type="Paper", resource_id=paper_id)

        # Get chunks needing embedding (skip already embedded chunks)
        chunks_query = select(Chunk).where(
            Chunk.paper_id == paper_id,
            Chunk.embedding.is_(None)
        ).order_by(Chunk.chunk_index.asc())
        result = await db.execute(chunks_query)
        unembedded_chunks = list(result.scalars().all())

        if not unembedded_chunks:
            logger.info(f"All chunks already embedded for paper ID: {paper_id}")
            total_query = select(func.count(Chunk.id)).where(Chunk.paper_id == paper_id)
            return (await db.execute(total_query)).scalar() or 0

        embedder = get_embedding_service()
        texts = [c.text for c in unembedded_chunks]

        logger.info(f"Generating vector embeddings for {len(texts)} unembedded chunks of paper '{paper.filename}'...")
        embeddings = embedder.embed_batch(texts)

        for chunk, vec in zip(unembedded_chunks, embeddings):
            chunk.embedding = vec

        await db.commit()
        logger.info(f"Successfully saved {len(embeddings)} vector embeddings for paper ID: {paper_id}")
        return len(embeddings)

    @staticmethod
    async def search_vector_similarity(
        db: AsyncSession,
        query_text: str,
        top_k: int = 5,
        paper_id_filter: Optional[str] = None,
        min_similarity_threshold: float = 0.20
    ) -> List[VectorSearchResult]:
        """
        Embeds query text and performs Cosine Distance vector search against pgvector chunk embeddings.
        """
        if not query_text or not query_text.strip():
            return []

        embedder = get_embedding_service()
        query_vector = embedder.embed_text(query_text)

        # pgvector cosine distance: Chunk.embedding.cosine_distance(query_vector)
        # Similarity score = 1 - cosine_distance
        cosine_dist = Chunk.embedding.cosine_distance(query_vector)
        similarity_score = (1 - cosine_dist).label("similarity_score")

        stmt = (
            select(Chunk, similarity_score, Paper.title, Paper.filename)
            .outerjoin(Paper, Chunk.paper_id == Paper.id)
            .where(Chunk.embedding.is_not(None))
        )

        if paper_id_filter:
            stmt = stmt.where(Chunk.paper_id == paper_id_filter)

        stmt = stmt.order_by(cosine_dist.asc()).limit(top_k)

        try:
            result = await db.execute(stmt)
            rows = result.all()
        except Exception as e:
            logger.warning(f"Vector search database query failed (PostgreSQL may be offline): {e}")
            return []

        search_results: List[VectorSearchResult] = []
        for chunk, score, p_title, p_filename in rows:
            sim = round(float(score), 4)
            title_str = p_title or p_filename or chunk.paper_id
            if sim >= min_similarity_threshold:
                search_results.append(
                    VectorSearchResult(
                        chunk_id=chunk.id,
                        paper_id=chunk.paper_id,
                        page_number=chunk.page_number,
                        section_name=chunk.section_name,
                        text=chunk.text,
                        similarity_score=sim,
                        paper_title=title_str
                    )
                )

        logger.info(f"Vector search for '{query_text[:40]}...' returned {len(search_results)} matching chunks.")
        return search_results
