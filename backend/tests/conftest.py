"""Pytest configuration and test fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.rate_limiter import rate_limiter
from app.main import app
from app.tasks.celery_app import celery_app

# Enable eager execution for Celery during automated test runs
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = False


@pytest.fixture(autouse=True)
def reset_rate_limiter_fixture():
    """Reset rate limiter state before and after every test."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def async_client():
    """Async HTTP client bound to the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
