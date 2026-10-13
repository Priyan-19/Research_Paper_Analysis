"""
Background paper processing pipeline worker.
Handles PDF extraction, semantic chunking, vector embedding indexing, and Knowledge Graph building.
"""
from typing import Dict, Any, Optional
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import SemanticChunker
from app.embeddings.vector_store import VectorStoreService
from app.graph.extractor import GraphExtractor
from app.graph.neo4j_builder import Neo4jGraphBuilder
from app.schemas.graph import KnowledgeGraphExtractionResult


class PaperProcessingWorker:
    """
    Background worker for asynchronous research paper ingestion and processing.
    """

    @classmethod
    async def process_paper(
        cls,
        paper_id: str,
        file_path: str,
        title: str = "Untitled Paper",
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end background ingestion pipeline for a research paper:
        1. Extract text pages from PDF
        2. Chunks pages into semantic units
        3. Generates vector embeddings for vector store (if DB session provided)
        4. Extracts Knowledge Graph entities/relationships & persists to Neo4j
        """
        logger.info(f"[Worker] Starting background processing for Paper ID '{paper_id}' ({file_path})")

        result_summary: Dict[str, Any] = {
            "paper_id": paper_id,
            "status": "PROCESSING",
            "pages_count": 0,
            "chunks_count": 0,
            "embeddings_generated": 0,
            "graph_entities": 0,
            "graph_relationships": 0,
            "error": None
        }

        try:
            full_text = ""
            chunks_count = 0

            # 1. Reuse existing database chunks if DB session supplied
            if db is not None:
                from sqlalchemy import select
                from app.models.paper import Chunk
                chunks_res = await db.execute(
                    select(Chunk).where(Chunk.paper_id == paper_id).order_by(Chunk.chunk_index.asc())
                )
                db_chunks = list(chunks_res.scalars().all())
                if db_chunks:
                    full_text = "\n\n".join(c.text for c in db_chunks)
                    chunks_count = len(db_chunks)

            # 2. Fallback to PDF extraction if not already in DB
            if not full_text:
                pages = PDFLoader.extract_pages(file_path)
                result_summary["pages_count"] = len(pages)
                full_text = "\n\n".join(p.text for p in pages)
                chunker = SemanticChunker(target_chunk_size=700, chunk_overlap=100)
                chunks = chunker.chunk_pages(pages)
                chunks_count = len(chunks)

            result_summary["chunks_count"] = chunks_count

            # 3. Vector Embedding Generation (skip if already generated)
            if db is not None:
                embedded_count = await VectorStoreService.embed_paper_chunks(db=db, paper_id=paper_id)
                result_summary["embeddings_generated"] = embedded_count

            # 4. Knowledge Graph Extraction
            graph_data: KnowledgeGraphExtractionResult = await GraphExtractor.extract_graph(
                text=full_text,
                paper_title=title,
                paper_id=paper_id
            )
            result_summary["graph_entities"] = len(graph_data.entities)
            result_summary["graph_relationships"] = len(graph_data.relationships)

            # 5. Persist to Neo4j Graph DB
            try:
                graph_persisted = await Neo4jGraphBuilder.persist_paper_graph(
                    paper_id=paper_id,
                    paper_title=title,
                    graph_data=graph_data
                )
                result_summary["graph_persisted"] = graph_persisted
            except Exception as graph_err:
                logger.warning(f"[Worker] Neo4j graph persistence skipped/failed: {str(graph_err)}")
                result_summary["graph_persisted"] = False

            result_summary["status"] = "COMPLETED"
            logger.info(f"[Worker] Successfully finished processing Paper ID '{paper_id}'")
            return result_summary

        except Exception as e:
            logger.error(f"[Worker] Processing failed for Paper ID '{paper_id}': {str(e)}")
            result_summary["status"] = "FAILED"
            result_summary["error"] = str(e)
            return result_summary


def run_paper_processing_task(
    paper_id: str,
    file_path: str,
    title: str = "Untitled Paper"
) -> Dict[str, Any]:
    """
    Synchronous entrypoint for background worker tasks (e.g. Celery / FastAPI background task).
    """
    return asyncio.run(PaperProcessingWorker.process_paper(
        paper_id=paper_id,
        file_path=file_path,
        title=title
    ))
