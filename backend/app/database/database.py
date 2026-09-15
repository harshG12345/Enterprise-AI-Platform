"""Database connection engine and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config.settings import get_settings

settings = get_settings()

is_testing = (
    settings.APP_ENV == "testing"
    or getattr(settings, "ENVIRONMENT", None) == "testing"
    or settings.DATABASE_URL.startswith("sqlite")
)

# Async Engine for FastAPI Request Handlers
async_engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
    "pool_pre_ping": True,
}
if is_testing:
    async_engine_kwargs["poolclass"] = NullPool
else:
    async_engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    async_engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
    async_engine_kwargs["pool_timeout"] = settings.DATABASE_POOL_TIMEOUT
    async_engine_kwargs["pool_recycle"] = settings.DATABASE_POOL_RECYCLE

async_engine = create_async_engine(settings.DATABASE_URL, **async_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync Engine for Celery Workers and Alembic Migrations
sync_engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
    "pool_pre_ping": True,
}
if is_testing:
    sync_engine_kwargs["poolclass"] = NullPool
else:
    sync_engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    sync_engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
    sync_engine_kwargs["pool_timeout"] = settings.DATABASE_POOL_TIMEOUT
    sync_engine_kwargs["pool_recycle"] = settings.DATABASE_POOL_RECYCLE

if settings.DATABASE_URL_SYNC.startswith("sqlite"):
    sync_engine_kwargs["connect_args"] = {"check_same_thread": False}

sync_engine = create_engine(settings.DATABASE_URL_SYNC, **sync_engine_kwargs)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection providing an isolated async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db() -> Session:
    """Helper providing an isolated sync database session for background workers."""
    session = SyncSessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise
