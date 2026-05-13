from typing import AsyncGenerator
from fastapi import Request
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_async_session

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Dependency for getting a Redis client.
    """
    client = aioredis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting a scoped DB session per request.
    Wraps the database module's session generator.
    """
    async for session in get_async_session():
        yield session

async def get_current_user_id(request: Request) -> str:
    """
    Dependency for getting the current user ID from the session/context.
    (Placeholder — will be replaced with real auth logic)
    """
    return "anonymous_user"
