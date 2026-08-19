"""/api/companies (issue #12)."""

import pytest
from app.db import Base, get_engine
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client(temp_db):
    Base.metadata.create_all(get_engine())
    with TestClient(app) as client:
        yield client


def test_create_company_happy_path(client) -> None:
    response = client.post("/api/companies", json={"name": "Acme"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Acme"
    assert body["status"] == "watchlist"
    assert body["url"] is None
    assert body["id"] is not None


def test_created_company_is_durable_across_requests(client) -> None:
    created = client.post("/api/companies", json={"name": "Acme"}).json()

    # A second, independent request — proves the write was committed, not
    # just visible within the create request's own session.
    response = client.get(f"/api/companies/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Acme"


def test_get_nonexistent_company_is_404(client) -> None:
    assert client.get("/api/companies/999").status_code == 404


def test_list_all_companies(client) -> None:
    client.post("/api/companies", json={"name": "Acme"})
    client.post("/api/companies", json={"name": "Beta"})

    response = client.get("/api/companies")

    assert response.status_code == 200
    assert {c["name"] for c in response.json()} == {"Acme", "Beta"}


def test_list_filters_by_name_and_status(client) -> None:
    client.post("/api/companies", json={"name": "Acme Corp", "status": "watchlist"})
    client.post("/api/companies", json={"name": "Beta Inc", "status": "active"})

    by_name = client.get("/api/companies", params={"name": "Acme"}).json()
    assert [c["name"] for c in by_name] == ["Acme Corp"]

    by_status = client.get("/api/companies", params={"status": "active"}).json()
    assert [c["name"] for c in by_status] == ["Beta Inc"]

    by_both = client.get("/api/companies", params={"name": "Beta", "status": "active"}).json()
    assert [c["name"] for c in by_both] == ["Beta Inc"]


def test_update_happy_path(client) -> None:
    created = client.post("/api/companies", json={"name": "Acme"}).json()

    response = client.patch(f"/api/companies/{created['id']}", json={"status": "active"})

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_partial_update_does_not_wipe_other_fields(client) -> None:
    created = client.post(
        "/api/companies", json={"name": "Acme", "url": "https://acme.example"}
    ).json()

    response = client.patch(f"/api/companies/{created['id']}", json={"status": "active"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert body["url"] == "https://acme.example"  # untouched, not wiped to null


def test_update_nonexistent_company_is_404(client) -> None:
    response = client.patch("/api/companies/999", json={"status": "active"})
    assert response.status_code == 404


def test_create_missing_name_is_422(client) -> None:
    response = client.post("/api/companies", json={})
    assert response.status_code == 422


def test_create_invalid_status_is_422(client) -> None:
    response = client.post("/api/companies", json={"name": "Acme", "status": "not-a-status"})
    assert response.status_code == 422
