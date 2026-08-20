"""GET /api/funnel (issue #22)."""

import datetime

import pytest
from app.db import Base, get_engine
from app.main import app
from app.models import StageEvent
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def client(temp_db):
    Base.metadata.create_all(get_engine())
    with TestClient(app) as client:
        yield client


@pytest.fixture
def company_id(client) -> int:
    return client.post("/api/companies", json={"name": "Acme"}).json()["id"]


def _stages(response) -> dict:
    return {row["stage"]: row for row in response.json()["stages"]}


def test_unfiltered_funnel_counts_from_stage_event_history(client, company_id) -> None:
    # A referral jump: outreach -> screen directly, skipping replied.
    jumper = client.post("/api/threads", json={"company_id": company_id}).json()["id"]
    client.post(f"/api/threads/{jumper}/stage", json={"to": "screen"})

    # A normal advance to replied.
    normal = client.post("/api/threads", json={"company_id": company_id}).json()["id"]
    client.post(f"/api/threads/{normal}/stage", json={"to": "replied"})

    stages = _stages(client.get("/api/funnel"))

    assert stages["replied"]["count"] == 1
    assert stages["screen"]["count"] == 1  # counted even though it skipped replied


def test_funnel_sliced_by_motion(client, company_id) -> None:
    cold = client.post(
        "/api/threads", json={"company_id": company_id, "motion": "cold_outreach"}
    ).json()["id"]
    client.post(f"/api/threads/{cold}/stage", json={"to": "screen"})

    warm = client.post(
        "/api/threads", json={"company_id": company_id, "motion": "warm_outreach"}
    ).json()["id"]
    client.post(f"/api/threads/{warm}/stage", json={"to": "screen"})

    stages = _stages(client.get("/api/funnel", params={"motion": "cold_outreach"}))

    assert stages["screen"]["count"] == 1


def test_funnel_windowed_to_7_days(client, company_id) -> None:
    old = client.post("/api/threads", json={"company_id": company_id}).json()["id"]
    recent = client.post("/api/threads", json={"company_id": company_id}).json()["id"]
    client.post(f"/api/threads/{old}/stage", json={"to": "screen"})
    client.post(f"/api/threads/{recent}/stage", json={"to": "screen"})

    with Session(get_engine()) as session:
        stale_event = session.query(StageEvent).filter(StageEvent.thread_id == old).first()
        assert stale_event is not None
        stale_event.occurred_at -= datetime.timedelta(days=10)
        session.commit()

    stages = _stages(client.get("/api/funnel", params={"window": "7d"}))

    assert stages["screen"]["count"] == 1  # only the recent one


def test_conversion_is_null_when_denominator_is_zero(client, company_id) -> None:
    # A referral jump within a motion filter that excludes any "replied" thread.
    jumper = client.post(
        "/api/threads", json={"company_id": company_id, "motion": "cold_outreach"}
    ).json()["id"]
    client.post(f"/api/threads/{jumper}/stage", json={"to": "screen"})

    stages = _stages(client.get("/api/funnel", params={"motion": "cold_outreach"}))

    assert stages["replied"]["count"] == 0
    assert stages["screen"]["count"] == 1
    assert stages["screen"]["conversion_from_previous"] is None


def test_first_stage_has_null_conversion(client, company_id) -> None:
    thread_id = client.post("/api/threads", json={"company_id": company_id}).json()["id"]
    client.post(f"/api/threads/{thread_id}/stage", json={"to": "replied"})

    stages = _stages(client.get("/api/funnel"))

    assert stages["outreach"]["conversion_from_previous"] is None


def test_contribution_survives_the_thread_later_closing(client, company_id) -> None:
    thread_id = client.post("/api/threads", json={"company_id": company_id}).json()["id"]
    client.post(f"/api/threads/{thread_id}/stage", json={"to": "interview"})
    client.post(f"/api/threads/{thread_id}/stage", json={"to": "rejected"})

    stages = _stages(client.get("/api/funnel"))

    assert stages["interview"]["count"] == 1


def test_funnel_reflects_the_shared_demo_dataset(client, demo_data) -> None:
    """Issue #39 — a smoke test against the shared, realistic fixture,
    alongside (not replacing) the precise boundary tests above."""
    stages = _stages(client.get("/api/funnel"))

    assert stages["replied"]["count"] >= 1
    assert stages["offer"]["count"] >= 1
    non_zero_stages = [s["stage"] for s in stages.values() if s["count"] > 0]
    assert len(non_zero_stages) >= 3
