from fastapi import APIRouter, Request
from typing import Any
import redis.asyncio as aioredis
from sqlalchemy import text
from pinecone import Pinecone
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.database import async_session_maker
from app.schemas.health import HealthStatus, ReadinessStatus
from loguru import logger

router = APIRouter()

@router.get("/", response_model=HealthStatus)
@limiter.limit("100/minute")
async def liveness_check(request: Request):
    """
    Simple liveness check (Health).
    """
    return HealthStatus(status="ok", version=settings.VERSION)

@router.get("/ready", response_model=ReadinessStatus)
@limiter.limit("10/minute")
async def readiness_check(request: Request):
    """
    Readiness check (DB + Redis + Pinecone connectivity).
    """
    checks = {
        "database": "unknown",
        "redis": "unknown",
        "pinecone": "unknown"
    }
    
    # Check Database (Supabase PostgreSQL)
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = "failed"

    # Check Redis
    try:
        r = aioredis.Redis.from_url(settings.REDIS_URL)
        async with r:
            await r.ping()  # type: ignore
        checks["redis"] = "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        checks["redis"] = "failed"

    # Check Pinecone
    try:
        if settings.PINECONE_API_KEY:
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            pc.list_indexes()
            checks["pinecone"] = "ok"
        else:
            checks["pinecone"] = "skipped (no API key)"
    except Exception as e:
        logger.error(f"Pinecone health check failed: {e}")
        checks["pinecone"] = "failed"

    overall_status = "ok" if all(v in ["ok", "skipped (no API key)"] for v in checks.values()) else "partial_failure"
    
    return ReadinessStatus(status=overall_status, checks=checks)
