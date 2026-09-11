import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database.postgres import Base


class ProcessingStatus(str):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Paper(Base):
    """
    SQLAlchemy ORM Model representing an ingested research paper.
    """
    __tablename__ = "papers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    
    # Metadata fields
    title = Column(String(512), nullable=True)
    authors = Column(JSON, nullable=True, default=list)  # List of author names
    abstract = Column(Text, nullable=True)
    publication_year = Column(Integer, nullable=True)
    total_pages = Column(Integer, nullable=False, default=0)
    
    # Status & Timestamps
    status = Column(String(32), nullable=False, default=ProcessingStatus.PENDING)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    chunks = relationship("Chunk", back_populates="paper", cascade="all, delete-orphan", order_by="Chunk.chunk_index")
    jobs = relationship("ProcessingJob", back_populates="paper", cascade="all, delete-orphan")


class Chunk(Base):
    """
    SQLAlchemy ORM Model representing a semantic text chunk extracted from a paper.
    """
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    chunk_index = Column(Integer, nullable=False, index=True)
    page_number = Column(Integer, nullable=False, default=1)
    section_name = Column(String(255), nullable=False, default="General")
    
    text = Column(Text, nullable=False)
    char_length = Column(Integer, nullable=False, default=0)
    token_count = Column(Integer, nullable=False, default=0)
    
    # Vector embedding (384 dimensions for all-MiniLM-L6-v2, expandable for other models)
    embedding = Column(Vector(384), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    paper = relationship("Paper", back_populates="chunks")


class ProcessingJob(Base):
    """
    SQLAlchemy ORM Model tracking background ingestion jobs.
    """
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    paper_id = Column(String(36), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String(32), nullable=False, default=ProcessingStatus.PENDING)
    current_step = Column(String(128), nullable=True)
    progress_percentage = Column(Float, nullable=False, default=0.0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    paper = relationship("Paper", back_populates="jobs")
