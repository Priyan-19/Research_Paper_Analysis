# pyrefly: ignore [missing-import]
from fastapi import APIRouter, status
from app.core.config import settings
from app.database.postgres import check_postgres_health
from app.database.neo4j import neo4j_client
from app.database.redis import redis_client
from app.schemas.health import SystemHealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Comprehensive Health Check",
    description="Verifies operational state of API and database connections (PostgreSQL + pgvector, Neo4j, Redis)."
)
async def health_check():
    postgres_health = await check_postgres_health()
    neo4j_health = await neo4j_client.check_health()
    redis_health = await redis_client.check_health()

    # Determine overall status
    is_healthy = (
        postgres_health.get("connected", False) and
        neo4j_health.get("connected", False)
    )

    overall_status = "healthy" if is_healthy else "degraded"

    return SystemHealthResponse(
        status=overall_status,
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        services={
            "postgresql": postgres_health,
            "neo4j": neo4j_health,
            "redis": redis_health
        }
    )
