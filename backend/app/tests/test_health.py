import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """
    Test the liveness health check endpoint.
    """
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient, mock_redis):
    """
    Test the readiness check endpoint.
    """
    # Mock redis ping
    mock_redis.ping.return_value = True
    
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["checks"]["redis"] == "ok"
    assert data["checks"]["database"] == "ok"
