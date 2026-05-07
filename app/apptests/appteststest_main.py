import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_root_json():
    """API-запрос к корню возвращает JSON"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "timestamp" in data
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_root_html():
    """Запрос из браузера к корню возвращает HTML с секундомером"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert "Спортивный секундомер" in response.text
    assert '<button id="startBtn"' in response.text
    assert '<button id="lapBtn"' in response.text
    assert 'id="display"' in response.text


@pytest.mark.asyncio
async def test_healthz():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}