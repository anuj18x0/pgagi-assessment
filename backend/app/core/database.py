from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Async engine configured for Supabase pgBouncer
# prepared_statement_cache_size=0 is critical for pgBouncer transaction mode
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,     # Recycle stale connections every 5 min
)

# Session factory — produces scoped AsyncSession instances
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    """
    Declarative base for all ORM models.
    All models should inherit from this class.
    """
    pass

async def get_async_session():
    """
    Yield a scoped AsyncSession per request.
    Used as a FastAPI dependency.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def dispose_engine():
    """
    Gracefully close all connections in the pool.
    Called during application shutdown.
    """
    await engine.dispose()
