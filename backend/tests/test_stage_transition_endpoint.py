"""POST /api/threads/{id}/stage (issue #18)."""

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


def test_normal_advance(client, thread_id) -> None:
    response = client.post(f"/api/threads/{thread_id}/stage", json={"to": "replied"})

    assert response.status_code == 201
    body = response.json()
    assert body["thread"]["stage"] == "replied"
    assert body["thread"]["status"] == "open"
    assert body["stage_event"]["from_stage"] == "outreach"
    assert body["stage_event"]["to_stage"] == "replied"


def test_referral_jump_outreach_straight_to_screen(client, thread_id) -> None:
    response = client.post(f"/api/threads/{thread_id}/stage", json={"to": "screen"})

    assert response.status_code == 201
    body = response.json()
    assert body["thread"]["stage"] == "screen"
    assert body["stage_event"]["from_stage"] == "outreach"
    assert body["stage_event"]["to_stage"] == "screen"


def test_backward_correction(client, thread_id) -> None:
    client.post(f"/api/threads/{thread_id}/stage", json={"to": "screen"})
    client.post(f"/api/threads/{thread_id}/stage", json={"to": "interview"})

    response = client.post(f"/api/threads/{thread_id}/stage", json={"to": "screen"})

    body = response.json()
    assert body["thread"]["stage"] == "screen"
    assert body["stage_event"]["from_stage"] == "interview"
    assert body["stage_event"]["to_stage"] == "screen"


def test_closing_as_rejected_leaves_stage_unchanged(client, thread_id) -> None:
    client.post(f"/api/threads/{thread_id}/stage", json={"to": "interview"})

    response = client.post(f"/api/threads/{thread_id}/stage", json={"to": "rejected"})

    body = response.json()
    assert body["thread"]["status"] == "rejected"
    assert body["thread"]["stage"] == "interview"  # unchanged, not reset
    assert body["thread"]["closed_at"] is not None
    assert body["stage_event"]["from_stage"] == "interview"
    assert body["stage_event"]["to_stage"] == "rejected"


def test_stage_move_after_terminal_reopens_the_thread(client, thread_id) -> None:
    client.post(f"/api/threads/{thread_id}/stage", json={"to": "rejected"})

    response = client.post(f"/api/threads/{thread_id}/stage", json={"to": "screen"})

    body = response.json()
    assert body["thread"]["status"] == "open"
    assert body["thread"]["stage"] == "screen"
    assert body["stage_event"]["from_stage"] == "rejected"
    assert body["stage_event"]["to_stage"] == "screen"


def test_stage_change_on_nonexistent_thread_is_404(client) -> None:
    response = client.post("/api/threads/999/stage", json={"to": "screen"})
    assert response.status_code == 404


def test_stage_event_appears_in_thread_detail(client, thread_id) -> None:
    client.post(f"/api/threads/{thread_id}/stage", json={"to": "replied", "note": "they replied"})

    detail = client.get(f"/api/threads/{thread_id}").json()
    assert len(detail["stage_events"]) == 1
    assert detail["stage_events"][0]["note"] == "they replied"
