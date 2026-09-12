"""Unit tests for database session lifecycle and transaction boundaries."""

import pytest
from sqlalchemy import text

from app.database.database import AsyncSessionLocal, get_sync_db


@pytest.mark.asyncio
async def test_async_session_execution():
    """Verify async database session executes raw queries."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1 AS alive"))
        row = result.mappings().one()
        assert row["alive"] == 1


def test_sync_session_execution():
    """Verify sync database session for background workers executes queries."""
    session = get_sync_db()
    try:
        result = session.execute(text("SELECT 1 AS alive"))
        row = result.mappings().one()
        assert row["alive"] == 1
    finally:
        session.close()
