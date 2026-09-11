from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger


class RedisClient:
    """Async Redis Client for Caching & Task Queue Support."""
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Initializes Redis connection pool."""
        try:
            self.redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5.0
            )
            logger.info(f"Initialized Redis client connection to {settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")

    async def close(self):
        """Closes Redis connection pool."""
        if self.redis:
            await self.redis.close()
            logger.info("Closed Redis connection.")

    async def check_health(self) -> dict:
        """Verifies Redis ping response."""
        if not self.redis:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": "Client not initialized"
            }
        try:
            pong = await self.redis.ping()
            if pong:
                return {
                    "status": "healthy",
                    "connected": True,
                    "url": settings.REDIS_URL
                }
            return {
                "status": "unhealthy",
                "connected": False,
                "error": "Ping failed"
            }
        except Exception as e:
            logger.error(f"Redis Health Check Failed: {str(e)}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }


redis_client = RedisClient()
