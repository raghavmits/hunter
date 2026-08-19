"""The app factory mounts /api and allows the Vite dev origin."""

from app.main import VITE_DEV_ORIGIN, app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_allows_vite_dev_origin() -> None:
    response = client.get("/api/health", headers={"Origin": VITE_DEV_ORIGIN})

    assert response.headers["access-control-allow-origin"] == VITE_DEV_ORIGIN


def test_rejects_other_origins() -> None:
    response = client.get("/api/health", headers={"Origin": "http://evil.example"})

    assert "access-control-allow-origin" not in response.headers
