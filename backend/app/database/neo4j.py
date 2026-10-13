from typing import Optional
import asyncio
# pyrefly: ignore [missing-import]
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.core.config import settings
from app.core.logging import logger


class Neo4jClient:
    """Async Neo4j Graph Database Client Driver."""
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self):
        """Initializes or re-initializes the Neo4j Async Driver connection pool."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if self.driver is not None and self._loop != current_loop:
            try:
                await self.driver.close()
            except Exception:
                pass
            self.driver = None

        if self.driver is None:
            try:
                self.driver = AsyncGraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                self._loop = current_loop
                logger.info(f"Initialized Neo4j driver connection to {settings.NEO4J_URI}")
            except Exception as e:
                logger.error(f"Failed to create Neo4j driver: {str(e)}")

    async def close(self):
        """Closes the Neo4j driver connection pool."""
        if self.driver:
            try:
                await self.driver.close()
            except Exception:
                pass
            self.driver = None
            self._loop = None
            logger.info("Closed Neo4j driver connection.")

    async def check_health(self) -> dict:
        """Verifies active connectivity to Neo4j graph cluster/database."""
        await self.connect()
        if not self.driver:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": "Driver not initialized"
            }
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 AS result")
                record = await result.single()
                if record and record["result"] == 1:
                    return {
                        "status": "healthy",
                        "connected": True,
                        "uri": settings.NEO4J_URI
                    }
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "error": "Unexpected ping response"
                }
        except Exception as e:
            logger.error(f"Neo4j Health Check Failed: {str(e)}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }


neo4j_client = Neo4jClient()


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_neo4j_session():
    """
    Context manager providing an AsyncSession from the initialized Neo4j driver.
    """
    await neo4j_client.connect()
    if not neo4j_client.driver:
        raise RuntimeError("Neo4j driver is not initialized and connection failed.")
    async with neo4j_client.driver.session() as session:
        yield session


