import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from typing import AsyncGenerator
from unittest.mock import MagicMock
from app.main import app
from app.core.dependencies import get_redis, get_db

# --- Mocks ---

@pytest.fixture
def mock_redis():
    """
    Fixture for mocking Redis.
    """
    mock = MagicMock()
    mock.ping.return_value = True
    return mock

@pytest.fixture
def mock_db():
    """
    Fixture for mocking the Database session.
    """
    return MagicMock()

# --- Dependency Overrides ---

@pytest_asyncio.fixture
async def client(mock_redis, mock_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Async test client with dependency overrides.
    """
    async def override_get_redis():
        yield mock_redis

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_redis] = override_get_redis
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()

# --- Config ---

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
