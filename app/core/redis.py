import redis.asyncio as aioredis
from app.core.config import settings

async def get_redis_client() -> aioredis.Redis:
    """Returns an async Redis client instance."""
    return aioredis.from_url(
        settings.REDIS_URL, 
        encoding="utf-8", 
        decode_responses=False
    )
