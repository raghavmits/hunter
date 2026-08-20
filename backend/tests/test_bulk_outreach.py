"""POST /api/threads/bulk-outreach (issue #34)."""

import datetime

import pytest
from app.db import Base, get_engine
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client(temp_db):
    Base.metadata.create_all(get_engine())
    with TestClient(app) as client:
        yield client


def test_all_rows_succeed(client) -> None:
    response = client.post(
        "/api/threads/bulk-outreach",
        json={
            "kind": "cold_outreach",
            "channel": "email",
            "rows": [
                {"company_name": "Acme"},
                {"company_name": "Zeta", "role_title": "Backend Engineer"},
            ],
        },
    )

    assert response.status_code == 201
    results = response.json()["results"]
    assert [r["success"] for r in results] == [True, True]
    assert [r["row_index"] for r in results] == [0, 1]
    assert all(r["thread_id"] is not None for r in results)

    threads = client.get("/api/threads").json()
    assert {t["company_name"] for t in threads} == {"Acme", "Zeta"}
    assert {t["role_title"] for t in threads} == {None, "Backend Engineer"}


def test_touch_logged_and_cadence_applied(client) -> None:
    response = client.post(
        "/api/threads/bulk-outreach",
        json={"kind": "cold_outreach", "channel": "email", "rows": [{"company_name": "Acme"}]},
    )
    thread_id = response.json()["results"][0]["thread_id"]

    thread = client.get(f"/api/threads/{thread_id}").json()
    assert len(thread["touches"]) == 1
    assert thread["touches"][0]["kind"] == "cold_outreach"
    assert thread["touches"][0]["direction"] == "outbound"
    assert thread["touches"][0]["channel"] == "email"
    assert thread["nudge_number"] == 1
    assert thread["next_follow_up_date"] is not None


def test_blank_company_name_fails_without_discarding_other_rows(client) -> None:
    response = client.post(
        "/api/threads/bulk-outreach",
        json={
            "kind": "cold_outreach",
            "channel": "email",
            "rows": [
                {"company_name": "Acme"},
                {"company_name": "   "},
                {"company_name": "Zeta"},
            ],
        },
    )

    assert response.status_code == 201
    results = response.json()["results"]
    assert [r["success"] for r in results] == [True, False, True]
    assert results[1]["error"] is not None
    assert results[1]["thread_id"] is None

    threads = client.get("/api/threads").json()
    assert {t["company_name"] for t in threads} == {"Acme", "Zeta"}


def test_nonexistent_contact_fails_row_without_creating_company(client) -> None:
    response = client.post(
        "/api/threads/bulk-outreach",
        json={
            "kind": "cold_outreach",
            "channel": "email",
            "rows": [{"company_name": "Ghost Co", "contact_id": 999}],
        },
    )

    assert response.status_code == 201
    result = response.json()["results"][0]
    assert result["success"] is False
    assert result["error"] is not None
    assert result["thread_id"] is None

    assert client.get("/api/threads").json() == []
    assert client.get("/api/companies", params={"name": "Ghost Co"}).json() == []


def test_repeated_company_name_matches_same_company(client) -> None:
    response = client.post(
        "/api/threads/bulk-outreach",
        json={
            "kind": "cold_outreach",
            "channel": "email",
            "rows": [{"company_name": "Acme"}, {"company_name": "Acme"}],
        },
    )

    assert response.status_code == 201
    threads = client.get("/api/threads").json()
    assert len(threads) == 2
    assert len({t["company_id"] for t in threads}) == 1
    assert len(client.get("/api/companies").json()) == 1


def test_shared_occurred_at_defaults_to_today(client) -> None:
    response = client.post(
        "/api/threads/bulk-outreach",
        json={"kind": "cold_outreach", "channel": "email", "rows": [{"company_name": "Acme"}]},
    )
    thread_id = response.json()["results"][0]["thread_id"]
    thread = client.get(f"/api/threads/{thread_id}").json()

    assert thread["touches"][0]["occurred_at"] == datetime.date.today().isoformat()


def test_empty_rows_rejected(client) -> None:
    response = client.post(
        "/api/threads/bulk-outreach", json={"kind": "cold_outreach", "channel": "email", "rows": []}
    )

    assert response.status_code == 422
