"""POST /api/threads — quick-add (issue #14)."""

import pytest
from app.db import Base, get_engine
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client(temp_db):
    Base.metadata.create_all(get_engine())
    with TestClient(app) as client:
        yield client


def test_create_from_a_new_company_name(client) -> None:
    response = client.post("/api/threads", json={"company_name": "Acme"})

    assert response.status_code == 201
    body = response.json()
    assert body["company_id"] is not None
    assert client.get(f"/api/companies/{body['company_id']}").json()["name"] == "Acme"


def test_create_from_an_existing_company_name_reuses_it(client) -> None:
    first = client.post("/api/threads", json={"company_name": "Acme"}).json()
    second = client.post("/api/threads", json={"company_name": "Acme"}).json()

    assert first["company_id"] == second["company_id"]
    assert len(client.get("/api/companies").json()) == 1  # no duplicate company


def test_create_from_an_existing_company_id(client) -> None:
    company = client.post("/api/companies", json={"name": "Acme"}).json()

    response = client.post("/api/threads", json={"company_id": company["id"]})

    assert response.status_code == 201
    assert response.json()["company_id"] == company["id"]


def test_create_with_a_contact_attached(client) -> None:
    company = client.post("/api/companies", json={"name": "Acme"}).json()
    contact = client.post(
        "/api/contacts", json={"full_name": "Jamie Doe", "company_id": company["id"]}
    ).json()

    response = client.post(
        "/api/threads", json={"company_id": company["id"], "contact_id": contact["id"]}
    )

    assert response.status_code == 201
    assert response.json()["contact_id"] == contact["id"]


def test_defaults_on_a_freshly_created_thread(client) -> None:
    response = client.post("/api/threads", json={"company_name": "Acme"})

    body = response.json()
    assert body["stage"] == "outreach"
    assert body["status"] == "open"
    assert body["nudge_number"] == 0
    assert body["follow_up_pinned"] is False
    assert body["referral_promised"] is False
    assert body["stage_entered_at"] is not None


def test_neither_company_field_is_422(client) -> None:
    response = client.post("/api/threads", json={})
    assert response.status_code == 422


def test_both_company_fields_is_422(client) -> None:
    response = client.post("/api/threads", json={"company_id": 1, "company_name": "Acme"})
    assert response.status_code == 422


def test_empty_company_name_is_422(client) -> None:
    assert client.post("/api/threads", json={"company_name": ""}).status_code == 422
    assert client.post("/api/threads", json={"company_name": "   "}).status_code == 422
    assert client.get("/api/companies").json() == []  # no garbage company created


def test_nonexistent_company_id_is_404(client) -> None:
    response = client.post("/api/threads", json={"company_id": 999})
    assert response.status_code == 404


def test_nonexistent_contact_id_is_404(client) -> None:
    company = client.post("/api/companies", json={"name": "Acme"}).json()

    response = client.post("/api/threads", json={"company_id": company["id"], "contact_id": 999})

    assert response.status_code == 404
