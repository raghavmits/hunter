"""/api/contacts (issue #13)."""

import pytest
from app.db import Base, get_engine
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client(temp_db):
    Base.metadata.create_all(get_engine())
    with TestClient(app) as client:
        yield client


@pytest.fixture
def company_id(client) -> int:
    return client.post("/api/companies", json={"name": "Acme"}).json()["id"]


def test_create_with_no_company(client) -> None:
    response = client.post("/api/contacts", json={"full_name": "Jamie Doe"})

    assert response.status_code == 201
    body = response.json()
    assert body["company_id"] is None
    assert body["full_name"] == "Jamie Doe"


def test_create_with_a_company(client, company_id) -> None:
    response = client.post(
        "/api/contacts", json={"full_name": "Jamie Doe", "company_id": company_id}
    )

    assert response.status_code == 201
    assert response.json()["company_id"] == company_id


def test_create_with_nonexistent_company_is_404(client) -> None:
    response = client.post("/api/contacts", json={"full_name": "Jamie Doe", "company_id": 999})
    assert response.status_code == 404


def test_create_invalid_source_is_422(client) -> None:
    response = client.post("/api/contacts", json={"full_name": "Jamie Doe", "source": "bogus"})
    assert response.status_code == 422


def test_create_invalid_warmth_is_422(client) -> None:
    response = client.post("/api/contacts", json={"full_name": "Jamie Doe", "warmth": "bogus"})
    assert response.status_code == 422


def test_create_empty_full_name_is_422(client) -> None:
    assert client.post("/api/contacts", json={"full_name": ""}).status_code == 422
    assert client.post("/api/contacts", json={"full_name": "   "}).status_code == 422


def test_list_filtered_by_company(client, company_id) -> None:
    client.post("/api/contacts", json={"full_name": "With Company", "company_id": company_id})
    client.post("/api/contacts", json={"full_name": "No Company"})

    unfiltered = client.get("/api/contacts").json()
    assert len(unfiltered) == 2

    filtered = client.get("/api/contacts", params={"company_id": company_id}).json()
    assert [c["full_name"] for c in filtered] == ["With Company"]


def test_get_nonexistent_contact_is_404(client) -> None:
    assert client.get("/api/contacts/999").status_code == 404


def test_update_happy_path(client) -> None:
    created = client.post("/api/contacts", json={"full_name": "Jamie Doe"}).json()

    response = client.patch(f"/api/contacts/{created['id']}", json={"warmth": "warm"})

    assert response.status_code == 200
    assert response.json()["warmth"] == "warm"


def test_partial_update_does_not_wipe_other_fields(client) -> None:
    created = client.post(
        "/api/contacts", json={"full_name": "Jamie Doe", "email": "jamie@example.com"}
    ).json()

    response = client.patch(f"/api/contacts/{created['id']}", json={"warmth": "warm"})

    assert response.status_code == 200
    body = response.json()
    assert body["warmth"] == "warm"
    assert body["email"] == "jamie@example.com"


def test_update_with_nonexistent_company_is_404(client) -> None:
    created = client.post("/api/contacts", json={"full_name": "Jamie Doe"}).json()

    response = client.patch(f"/api/contacts/{created['id']}", json={"company_id": 999})

    assert response.status_code == 404


def test_update_nonexistent_contact_is_404(client) -> None:
    response = client.patch("/api/contacts/999", json={"warmth": "warm"})
    assert response.status_code == 404
