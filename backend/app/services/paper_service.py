import uuid
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, or_
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ResourceNotFoundError, PDFProcessingError, DuplicatePaperError
from app.models.paper import Paper, Chunk, ProcessingJob, ProcessingStatus
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import SemanticChunker
from app.ingestion.metadata_extractor import MetadataExtractor
from app.database.postgres import AsyncSessionLocal


class PaperService:
    """
    Service class managing paper ingestion, chunking, storage, background processing, and user-scoped retrieval.
    """

    @staticmethod
    async def save_paper_initial(
        db: AsyncSession,
        file_bytes: bytes,
        original_filename: str,
        user_id: Optional[str] = None
    ) -> Paper:
        """
        Validates duplicate upload, writes PDF to disk, creates initial Paper and ProcessingJob records,
        and returns immediately so background processing can execute asynchronously.
        """
        file_size = len(file_bytes)
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Check for existing duplicate paper
        query = select(Paper).where(
            ((Paper.file_hash == file_hash) |
             ((Paper.filename == original_filename) & (Paper.file_size_bytes == file_size))) &
            (Paper.status != ProcessingStatus.FAILED)
        )
        if user_id:
            query = query.where(or_(Paper.user_id == user_id, Paper.user_id.is_(None)))

        existing_result = await db.execute(query)
        existing_paper = existing_result.scalars().first()

        if existing_paper:
            logger.warning(
                f"Duplicate paper upload prevented for '{original_filename}' "
                f"(Existing Paper ID: {existing_paper.id})"
            )
            raise DuplicatePaperError(
                filename=original_filename,
                existing_paper_id=existing_paper.id
            )

        paper_id = str(uuid.uuid4())
        safe_filename = f"{paper_id}_{original_filename}"
        file_path = Path(settings.UPLOAD_DIR) / safe_filename

        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # Create Paper Record
        paper = Paper(
            id=paper_id,
            filename=original_filename,
            file_path=str(file_path),
            file_size_bytes=file_size,
            file_hash=file_hash,
            user_id=user_id,
            status=ProcessingStatus.PROCESSING
        )
        db.add(paper)

        # Create initial ProcessingJob Record
        job = ProcessingJob(
            id=str(uuid.uuid4()),
            paper_id=paper_id,
            status=ProcessingStatus.PROCESSING,
            current_step="PDF Uploaded",
            progress_percentage=10.0
        )
        db.add(job)

        await db.commit()
        await db.refresh(paper)
        logger.info(f"Initialized paper record for '{original_filename}' (ID: {paper_id}, User: {user_id or 'Public'})")
        return paper

    @classmethod
    async def process_and_save_paper(
        cls,
        db: AsyncSession,
        file_bytes: bytes,
        original_filename: str,
        user_id: Optional[str] = None
    ) -> Paper:
        """Backward-compatible wrapper for paper upload."""
        return await cls.save_paper_initial(db, file_bytes, original_filename, user_id=user_id)

    @classmethod
    async def process_paper_background(cls, paper_id: str):
        """
        Asynchronous background task executing end-to-end PDF processing:
        PDF parsing (with tables & OCR) -> Metadata extraction -> Semantic Chunking ->
        Vector Embeddings -> Full-Paper Knowledge Graph extraction & Neo4j persistence.
        """
        logger.info(f"[Background Task] Beginning processing for Paper ID '{paper_id}'")
        async with AsyncSessionLocal() as db:
            paper_res = await db.execute(select(Paper).where(Paper.id == paper_id))
            paper = paper_res.scalar_one_or_none()
            if not paper:
                logger.error(f"[Background Task] Paper '{paper_id}' not found in database.")
                return

            job_res = await db.execute(
                select(ProcessingJob).where(ProcessingJob.paper_id == paper_id).order_by(ProcessingJob.created_at.desc())
            )
            job = job_res.scalars().first()
            if not job:
                job = ProcessingJob(id=str(uuid.uuid4()), paper_id=paper_id, status=ProcessingStatus.PROCESSING)
                db.add(job)

            try:
                # 1. Load PDF Pages (Table extraction & OCR enabled)
                job.current_step = "Parsing PDF Pages & Tables"
                job.progress_percentage = 25.0
                await db.commit()

                pages = PDFLoader.extract_pages(paper.file_path)
                paper.total_pages = len(pages)

                # 2. Extract Metadata
                metadata = MetadataExtractor.extract_metadata(pages, paper.filename)
                paper.title = metadata.get("title")
                paper.authors = metadata.get("authors", [])
                paper.abstract = metadata.get("abstract")
                paper.publication_year = metadata.get("publication_year")

                # 3. Generate Semantic Chunks
                job.current_step = "Generating Semantic Chunks"
                job.progress_percentage = 50.0
                await db.commit()

                chunker = SemanticChunker(target_chunk_size=700, chunk_overlap=100)
                chunk_datas = chunker.chunk_pages(pages)

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
                await db.commit()

                # 4. Generate Vector Embeddings
                job.current_step = "Generating Dense Vector Embeddings"
                job.progress_percentage = 75.0
                await db.commit()

                try:
                    from app.embeddings.vector_store import VectorStoreService
                    await VectorStoreService.embed_paper_chunks(db, paper_id)
                except Exception as emb_err:
                    logger.warning(f"[Background Task] Embedding generation warning for {paper_id}: {emb_err}")

                # 5. Extract Full-Paper Knowledge Graph & Persist to Neo4j
                job.current_step = "Building Knowledge Graph"
                job.progress_percentage = 90.0
                await db.commit()

                try:
                    from app.graph.extractor import GraphExtractor
                    from app.graph.neo4j_builder import Neo4jGraphBuilder

                    extraction = await GraphExtractor.extract_graph_from_chunks(
                        chunks=chunks,
                        paper_id=paper_id,
                        paper_title=paper.title or paper.filename
                    )
                    await Neo4jGraphBuilder.persist_paper_graph(
                        paper_id=paper_id,
                        paper_title=paper.title or paper.filename,
                        graph_data=extraction
                    )
                    logger.info(f"[Background Task] Persisted {len(extraction.entities)} entities and {len(extraction.relationships)} edges to Neo4j.")
                except Exception as graph_err:
                    logger.warning(f"[Background Task] Knowledge Graph build warning for {paper_id}: {graph_err}")

                # 6. Mark Completed
                paper.status = ProcessingStatus.COMPLETED
                job.status = ProcessingStatus.COMPLETED
                job.current_step = "Ingestion Complete"
                job.progress_percentage = 100.0
                await db.commit()
                logger.info(f"[Background Task] Successfully finished processing for paper '{paper.filename}' ({paper_id})")

            except Exception as e:
                paper.status = ProcessingStatus.FAILED
                paper.error_message = str(e)
                job.status = ProcessingStatus.FAILED
                job.error_message = str(e)
                job.current_step = "Failed"
                await db.commit()
                logger.error(f"[Background Task] Processing failed for paper {paper_id}: {str(e)}")

    @staticmethod
    async def process_and_save_paper(
        db: AsyncSession,
        file_bytes: bytes,
        original_filename: str,
        user_id: Optional[str] = None
    ) -> Paper:
        """
        Synchronous wrapper for legacy callers and direct script executions.
        """
        paper = await PaperService.save_paper_initial(db, file_bytes, original_filename, user_id=user_id)
        await PaperService.process_paper_background(paper.id)
        await db.refresh(paper)
        return paper

    @staticmethod
    async def list_papers(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[str] = None
    ) -> Tuple[List[Paper], int]:
        """Lists uploaded papers, scoped to user ownership or public legacy documents."""
        count_query = select(func.count(Paper.id))
        query = select(Paper).order_by(Paper.created_at.desc())

        if user_id:
            count_query = count_query.where(or_(Paper.user_id == user_id, Paper.user_id.is_(None)))
            query = query.where(or_(Paper.user_id == user_id, Paper.user_id.is_(None)))

        total = (await db.execute(count_query)).scalar() or 0
        result = await db.execute(query.offset(skip).limit(limit))
        papers = result.scalars().all()
        return list(papers), total

    @staticmethod
    async def get_paper_by_id(db: AsyncSession, paper_id: str, user_id: Optional[str] = None) -> Paper:
        """Retrieves paper by ID with ownership verification."""
        query = select(Paper).where(Paper.id == paper_id)
        result = await db.execute(query)
        paper = result.scalar_one_or_none()
        if not paper:
            raise ResourceNotFoundError(resource_type="Paper", resource_id=paper_id)

        # Enforce multi-tenancy: if paper is owned by a different user, deny access
        if user_id and paper.user_id and paper.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this research paper."
            )
        return paper

    @staticmethod
    async def get_paper_chunks(db: AsyncSession, paper_id: str, user_id: Optional[str] = None) -> List[Chunk]:
        """Retrieves all text chunks for a paper ordered by chunk_index with tenant check."""
        await PaperService.get_paper_by_id(db, paper_id, user_id=user_id)

        query = select(Chunk).where(Chunk.paper_id == paper_id).order_by(Chunk.chunk_index.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete_paper(db: AsyncSession, paper_id: str, user_id: Optional[str] = None) -> bool:
        """Deletes a paper from DB, disk, and Neo4j, validating user ownership."""
        paper = await PaperService.get_paper_by_id(db, paper_id, user_id=user_id)

        # Enforce ownership on deletion
        if user_id and paper.user_id and paper.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this research paper."
            )

        # Remove file from disk
        file_path = Path(paper.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass

        # Delete Neo4j graph triples for paper
        try:
            from app.database.neo4j import get_neo4j_session
            async with get_neo4j_session() as session:
                await session.run("MATCH ()-[r]->() WHERE r.paper_id = $paper_id DELETE r", paper_id=paper_id)
                await session.run("MATCH (p:Paper {id: $paper_id}) DETACH DELETE p", paper_id=paper_id)
        except Exception as neo_err:
            logger.warning(f"Neo4j cleanup warning for paper {paper_id}: {neo_err}")

        await db.delete(paper)
        await db.commit()
        return True

    @staticmethod
    async def get_paper_processing_status(
        db: AsyncSession,
        paper_id: str,
        user_id: Optional[str] = None
    ) -> ProcessingJob:
        """Retrieves background processing progress for a paper."""
        await PaperService.get_paper_by_id(db, paper_id, user_id=user_id)

        query = select(ProcessingJob).where(ProcessingJob.paper_id == paper_id).order_by(ProcessingJob.created_at.desc())
        res = await db.execute(query)
        job = res.scalars().first()
        if not job:
            raise ResourceNotFoundError(resource_type="ProcessingJob", resource_id=paper_id)
        return job
