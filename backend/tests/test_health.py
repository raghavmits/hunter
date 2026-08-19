"""GET /api/health returns the expected shape."""

from app import APP_NAME, __version__
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_returns_200_with_name_and_version() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"name": APP_NAME, "version": __version__}
