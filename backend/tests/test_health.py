import httpx
import pytest

from main import app


@pytest.mark.anyio
async def test_health_route_stays_available(anyio_backend: str) -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
