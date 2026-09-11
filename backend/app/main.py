from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_v1_router
from app.database.postgres import init_postgres_extensions
from app.database.neo4j import neo4j_client
from app.database.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan context manager for managing startup and shutdown tasks.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} (v{settings.VERSION})...")

    # Initialize Database Extensions & Connections
    await init_postgres_extensions()
    await neo4j_client.connect()
    await redis_client.connect()

    yield

    # Shutdown Database Connections
    logger.info("Shutting down database drivers...")
    await neo4j_client.close()
    await redis_client.close()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Set CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 Routes
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
