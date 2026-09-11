from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logging import logger

# Create SQLAlchemy Async Engine
engine = create_async_engine(
    settings.get_database_url(),
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an async PostgreSQL database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_postgres_health() -> dict:
    """
    Verifies PostgreSQL connection and checks if pgvector extension is available.
    """
    try:
        async with AsyncSessionLocal() as session:
            # Simple ping
            res = await session.execute(text("SELECT 1"))
            res.scalar()

            # Check for pgvector extension
            vector_check = await session.execute(
                text("SELECT count(*) FROM pg_extension WHERE extname = 'vector';")
            )
            has_vector = (vector_check.scalar() or 0) > 0

            return {
                "status": "healthy",
                "connected": True,
                "pgvector_enabled": has_vector
            }
    except Exception as e:
        logger.error(f"PostgreSQL Health Check Failed: {str(e)}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


async def init_postgres_extensions():
    """Attempts to create vector extension in PostgreSQL if supported, and initializes DB tables."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await session.commit()
            logger.info("Successfully ensured 'vector' extension is enabled in PostgreSQL.")
    except Exception as e:
        logger.warning(f"Could not automatically create 'vector' extension: {str(e)}")

    try:
        from app.models import Paper, Chunk, ProcessingJob  # noqa: F401
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Successfully initialized PostgreSQL database tables.")
    except Exception as e:
        logger.warning(f"Could not automatically create database tables: {str(e)}")

