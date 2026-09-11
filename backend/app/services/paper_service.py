import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ResourceNotFoundError, PDFProcessingError
from app.models.paper import Paper, Chunk, ProcessingJob, ProcessingStatus
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import SemanticChunker
from app.ingestion.metadata_extractor import MetadataExtractor


class PaperService:
    """
    Service class managing paper ingestion, chunking, storage, and retrieval.
    """
    @staticmethod
    async def process_and_save_paper(
        db: AsyncSession,
        file_bytes: bytes,
        original_filename: str
    ) -> Paper:
        """
        Saves PDF to disk, parses page content, extracts metadata, creates chunks, and persists to PostgreSQL.
        """
        paper_id = str(uuid.uuid4())
        safe_filename = f"{paper_id}_{original_filename}"
        file_path = Path(settings.UPLOAD_DIR) / safe_filename

        # 1. Save file to disk
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        file_size = len(file_bytes)

        # 2. Create Initial Paper Record
        paper = Paper(
            id=paper_id,
            filename=original_filename,
            file_path=str(file_path),
            file_size_bytes=file_size,
            status=ProcessingStatus.PROCESSING
        )
        db.add(paper)
        await db.commit()
        await db.refresh(paper)

        try:
            # 3. Load PDF Pages
            pages = PDFLoader.extract_pages(str(file_path))
            paper.total_pages = len(pages)

            # 4. Extract Metadata
            metadata = MetadataExtractor.extract_metadata(pages, original_filename)
            paper.title = metadata.get("title")
            paper.authors = metadata.get("authors", [])
            paper.abstract = metadata.get("abstract")
            paper.publication_year = metadata.get("publication_year")

            # 5. Generate Semantic Chunks
            chunker = SemanticChunker(target_chunk_size=700, chunk_overlap=100)
            chunk_datas = chunker.chunk_pages(pages)

            # 6. Save Chunks to Database
            chunks: List[Chunk] = []
            for cdata in chunk_datas:
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    paper_id=paper_id,
                    chunk_index=cdata.chunk_index,
                    page_number=cdata.page_number,
                    section_name=cdata.section_name,
                    text=cdata.text,
                    char_length=cdata.char_length,
                    token_count=cdata.token_count
                )
                chunks.append(chunk)

            db.add_all(chunks)
            paper.status = ProcessingStatus.COMPLETED
            await db.commit()
            await db.refresh(paper)

            # 7. Automatically generate vector embeddings for chunks
            try:
                from app.embeddings.vector_store import VectorStoreService
                await VectorStoreService.embed_paper_chunks(db, paper_id)
            except Exception as emb_err:
                logger.warning(f"Automatic embedding generation deferred for paper {paper_id}: {str(emb_err)}")

            logger.info(f"Successfully processed paper '{original_filename}' (ID: {paper_id}) with {len(chunks)} chunks.")
            return paper

        except Exception as e:
            paper.status = ProcessingStatus.FAILED
            paper.error_message = str(e)
            await db.commit()
            logger.error(f"Failed to process paper {original_filename}: {str(e)}")
            raise e

    @staticmethod
    async def list_papers(db: AsyncSession, skip: int = 0, limit: int = 50) -> tuple[List[Paper], int]:
        """Lists all uploaded papers with total count."""
        count_query = select(func.count(Paper.id))
        total = (await db.execute(count_query)).scalar() or 0

        query = select(Paper).order_by(Paper.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        papers = result.scalars().all()
        return list(papers), total

    @staticmethod
    async def get_paper_by_id(db: AsyncSession, paper_id: str) -> Paper:
        """Retrieves paper by ID or raises ResourceNotFoundError."""
        query = select(Paper).where(Paper.id == paper_id)
        result = await db.execute(query)
        paper = result.scalar_one_or_none()
        if not paper:
            raise ResourceNotFoundError(resource_type="Paper", resource_id=paper_id)
        return paper

    @staticmethod
    async def get_paper_chunks(db: AsyncSession, paper_id: str) -> List[Chunk]:
        """Retrieves all text chunks for a paper ordered by chunk_index."""
        # Ensure paper exists first
        await PaperService.get_paper_by_id(db, paper_id)

        query = select(Chunk).where(Chunk.paper_id == paper_id).order_by(Chunk.chunk_index.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete_paper(db: AsyncSession, paper_id: str) -> bool:
        """Deletes a paper from DB, removes physical file from disk, and removes Neo4j graph nodes/triples."""
        paper = await PaperService.get_paper_by_id(db, paper_id)

        # Remove file from disk if exists
        file_path = Path(paper.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass

        # Delete Neo4j graph triples & orphaned entities for paper
        try:
            from app.database.neo4j import get_neo4j_session
            async with get_neo4j_session() as session:
                await session.run("MATCH ()-[r]->() WHERE r.paper_id = $paper_id DELETE r", paper_id=paper_id)
                await session.run("MATCH (p:Paper {id: $paper_id}) DETACH DELETE p", paper_id=paper_id)
                await session.run("MATCH (e:Entity) WHERE NOT (e)--() DETACH DELETE e")
        except Exception as err:
            logger.warning(f"Neo4j deletion for paper {paper_id} skipped: {err}")

        # Delete from DB
        await db.delete(paper)
        await db.commit()
        logger.info(f"Deleted paper ID: {paper_id} and associated file.")
        return True

    @staticmethod
    async def delete_all_papers(db: AsyncSession) -> int:
        """Deletes all papers and chunks from PostgreSQL, disk files, and Neo4j graph database."""
        papers, count = await PaperService.list_papers(db, limit=1000)
        for p in papers:
            try:
                fp = Path(p.file_path)
                if fp.exists():
                    fp.unlink()
            except Exception:
                pass

        await db.execute(delete(Chunk))
        await db.execute(delete(Paper))
        await db.commit()

        try:
            from app.database.neo4j import get_neo4j_session
            async with get_neo4j_session() as session:
                await session.run("MATCH (n) DETACH DELETE n")
        except Exception as err:
            logger.warning(f"Neo4j clear all skipped: {err}")

        logger.info(f"Successfully cleared all {count} papers and database structures.")
        return count
