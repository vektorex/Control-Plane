from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.db.base import Base

# Engine configuration kwargs
engine_kwargs = {
    "echo": settings.DATABASE_ECHO,
    "future": True,
}

# Add pool size only if not using SQLite
if not settings.async_database_url.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_pre_ping": True,
    })

engine: AsyncEngine = create_async_engine(
    settings.async_database_url,
    **engine_kwargs,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession per request,
    handling rollback on unhandled exceptions and closing cleanly.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Create database tables if they do not exist (useful for testing or initial dev).
    """
    logger.info(f"[DB] Initializing tables on database engine: {engine.url.render_as_string(hide_password=True)}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Dispose engine connection pool upon application shutdown.
    """
    logger.info("[DB] Disposing database engine connection pool.")
    await engine.dispose()
