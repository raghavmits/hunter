"""GET /api/quotas (issue #20)."""

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


@pytest.fixture
def thread_id(client) -> int:
    company = client.post("/api/companies", json={"name": "Acme"}).json()
    return client.post("/api/threads", json={"company_id": company["id"]}).json()["id"]


def _log(client, thread_id: int, kind: str, direction: str) -> None:
    client.post(
        f"/api/threads/{thread_id}/touches",
        json={"kind": kind, "direction": direction, "channel": "email"},
    )


def test_empty_day_reads_zero_with_full_remaining(client) -> None:
    response = client.get("/api/quotas")

    assert response.status_code == 200
    body = response.json()
    assert body["cold_outreach_sent"] == {"count": 0, "target": 10, "remaining": 10}
    assert body["warm_intro_requests_sent"] == {"count": 0, "target": 6, "remaining": 6}
    assert body["cold_applications_submitted"] == {"count": 0, "target": 6, "remaining": 6}
    assert body["referral_asks_made"] == {"count": 0, "target": 3, "remaining": 3}


def test_mixed_touches_counted_correctly(client, thread_id) -> None:
    _log(client, thread_id, "cold_outreach", "outbound")
    _log(client, thread_id, "cold_outreach", "outbound")
    _log(client, thread_id, "warm_intro_request", "outbound")
    _log(client, thread_id, "application_submitted", "outbound")
    _log(client, thread_id, "referral_promised", "outbound")
    # Must not count: inbound touch of a matching kind
    _log(client, thread_id, "cold_outreach", "inbound")
    # Must not count: a kind with no quota mapping
    _log(client, thread_id, "post_interview", "outbound")

    body = client.get("/api/quotas").json()

    assert body["cold_outreach_sent"]["count"] == 2
    assert body["warm_intro_requests_sent"]["count"] == 1
    assert body["cold_applications_submitted"]["count"] == 1
    assert body["referral_asks_made"]["count"] == 1


def test_touch_on_a_different_day_is_not_counted(client, thread_id) -> None:
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    client.post(
        f"/api/threads/{thread_id}/touches",
        json={
            "kind": "cold_outreach",
            "direction": "outbound",
            "channel": "email",
            "occurred_at": yesterday,
        },
    )

    body = client.get("/api/quotas").json()

    assert body["cold_outreach_sent"]["count"] == 0


def test_remaining_floors_at_zero_when_target_exceeded(client, thread_id) -> None:
    for _ in range(4):
        _log(client, thread_id, "referral_promised", "outbound")  # target is 3

    body = client.get("/api/quotas").json()

    assert body["referral_asks_made"]["count"] == 4
    assert body["referral_asks_made"]["remaining"] == 0
