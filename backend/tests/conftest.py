"""
Pytest configuration and fixtures for backend tests.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def client():
    """Synchronous test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Asynchronous test client for FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
