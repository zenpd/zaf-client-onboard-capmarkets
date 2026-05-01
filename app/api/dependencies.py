"""FastAPI dependency factories — Redis, DB session."""
from __future__ import annotations
from redis.asyncio import Redis
from shared.config import get_settings

_redis_pool: Redis | None = None


async def get_redis() -> Redis:
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_pool


async def get_redis_direct() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)
