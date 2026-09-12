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
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    poolclass=NullPool if is_testing else None,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync Engine for Celery Workers and Alembic Migrations
sync_engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    poolclass=NullPool if is_testing else None,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL_SYNC.startswith("sqlite") else {},
)

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
