"""PATCH /api/threads/{id}/follow-up and POST /api/threads/{id}/snooze (issue #17)."""

import datetime

import pytest
from app.business_days import add_business_days
from app.db import Base, get_engine
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client(temp_db):
    Base.metadata.create_all(get_engine())
    with TestClient(app) as client:
        yield client


@pytest.fixture
def thread_id(client) -> int:
    company = client.post("/api/companies", json={"name": "Acme"}).json()
    return client.post("/api/threads", json={"company_id": company["id"]}).json()["id"]


def test_set_follow_up_pins_the_thread(client, thread_id) -> None:
    response = client.patch(
        f"/api/threads/{thread_id}/follow-up", json={"next_follow_up_date": "2030-06-15"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["next_follow_up_date"] == "2030-06-15"
    assert body["follow_up_pinned"] is True


def test_pinned_date_survives_a_later_outbound_touch(client, thread_id) -> None:
    client.patch(f"/api/threads/{thread_id}/follow-up", json={"next_follow_up_date": "2030-06-15"})

    response = client.post(
        f"/api/threads/{thread_id}/touches",
        json={"kind": "cold_outreach", "direction": "outbound", "channel": "email"},
    )

    assert response.json()["thread"]["next_follow_up_date"] == "2030-06-15"


def test_set_follow_up_on_nonexistent_thread_is_404(client) -> None:
    response = client.patch(
        "/api/threads/999/follow-up", json={"next_follow_up_date": "2030-06-15"}
    )
    assert response.status_code == 404


def test_snooze_skips_weekends(client, thread_id) -> None:
    response = client.post(f"/api/threads/{thread_id}/snooze", json={"business_days": 3})

    assert response.status_code == 200
    expected = add_business_days(datetime.date.today(), 3)
    assert response.json()["next_follow_up_date"] == expected.isoformat()


def test_snooze_pins_the_thread_and_survives_a_later_outbound_touch(client, thread_id) -> None:
    snoozed = client.post(f"/api/threads/{thread_id}/snooze", json={"business_days": 3}).json()
    assert snoozed["follow_up_pinned"] is True

    response = client.post(
        f"/api/threads/{thread_id}/touches",
        json={"kind": "cold_outreach", "direction": "outbound", "channel": "email"},
    )

    assert response.json()["thread"]["next_follow_up_date"] == snoozed["next_follow_up_date"]


def test_snooze_does_not_advance_nudge_or_log_a_touch(client, thread_id) -> None:
    response = client.post(f"/api/threads/{thread_id}/snooze", json={"business_days": 3})

    assert response.json()["nudge_number"] == 0
    detail = client.get(f"/api/threads/{thread_id}").json()
    assert detail["touches"] == []


def test_snooze_nonpositive_business_days_is_422(client, thread_id) -> None:
    assert (
        client.post(f"/api/threads/{thread_id}/snooze", json={"business_days": 0}).status_code
        == 422
    )
    assert (
        client.post(f"/api/threads/{thread_id}/snooze", json={"business_days": -1}).status_code
        == 422
    )


def test_snooze_on_nonexistent_thread_is_404(client) -> None:
    response = client.post("/api/threads/999/snooze", json={"business_days": 3})
    assert response.status_code == 404
