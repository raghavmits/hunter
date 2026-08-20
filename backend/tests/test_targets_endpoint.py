"""GET /api/targets (issue #21)."""

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


def _new_thread(client, company_id: int) -> int:
    return client.post("/api/threads", json={"company_id": company_id}).json()["id"]


def _log(client, thread_id: int, kind: str, direction: str) -> None:
    client.post(
        f"/api/threads/{thread_id}/touches",
        json={"kind": kind, "direction": direction, "channel": "email"},
    )


def _stage(client, thread_id: int, to: str) -> None:
    client.post(f"/api/threads/{thread_id}/stage", json={"to": to})


def test_empty_state_all_zero(client) -> None:
    response = client.get("/api/targets")

    assert response.status_code == 200
    body = response.json()
    assert body["new_connections_made"] == {
        "count": 0,
        "target": 60,
        "type": "input",
        "deadline": None,
    }
    assert body["offers"] == {"count": 0, "target": 3, "type": "outcome", "deadline": None}


# --- input counting path -------------------------------------------------


def test_input_counts_across_multiple_threads_and_kinds(client, company_id) -> None:
    a = _new_thread(client, company_id)
    b = _new_thread(client, company_id)
    _log(client, a, "cold_outreach", "outbound")
    _log(client, b, "cold_outreach", "outbound")
    _log(client, a, "warm_intro_request", "outbound")
    _log(client, a, "application_submitted", "outbound")
    # Must not count: inbound touch of a matching kind
    _log(client, a, "cold_outreach", "inbound")
    # Must not count: a kind with no target mapping
    _log(client, a, "post_interview", "outbound")

    body = client.get("/api/targets").json()

    assert body["new_connections_made"]["count"] == 2
    assert body["warm_outreach_with_acquaintances"]["count"] == 1
    assert body["cold_applications"]["count"] == 1


# --- outcome counting path -------------------------------------------------


def test_outcome_counts_distinct_threads_not_raw_events(client, company_id) -> None:
    thread_id = _new_thread(client, company_id)
    # Bounces through screen twice via a backward correction — must count once
    _stage(client, thread_id, "screen")
    _stage(client, thread_id, "interview")
    _stage(client, thread_id, "screen")

    body = client.get("/api/targets").json()

    assert body["screens_recruiter_calls"]["count"] == 1
    assert body["interviews"]["count"] == 1


def test_outcome_contribution_survives_the_thread_later_closing(client, company_id) -> None:
    thread_id = _new_thread(client, company_id)
    _stage(client, thread_id, "interview")
    _stage(client, thread_id, "rejected")

    body = client.get("/api/targets").json()

    assert body["interviews"]["count"] == 1


def test_outcome_counts_separate_threads_separately(client, company_id) -> None:
    a = _new_thread(client, company_id)
    b = _new_thread(client, company_id)
    _stage(client, a, "interview")
    _stage(client, b, "interview")

    body = client.get("/api/targets").json()

    assert body["interviews"]["count"] == 2


def test_targets_reflect_the_shared_demo_dataset(client, demo_data) -> None:
    """Issue #39 — a smoke test against the shared, realistic fixture,
    alongside (not replacing) the precise boundary tests above."""
    body = client.get("/api/targets").json()

    assert body["new_connections_made"]["count"] >= 1
    assert body["screens_recruiter_calls"]["count"] >= 1
    assert body["interviews"]["count"] >= 1
    assert body["offers"]["count"] >= 1
