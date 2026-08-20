"""GET /api/threads and GET /api/threads/{id} (issue #15)."""

import datetime

import pytest
from app.db import Base, get_engine
from app.main import app
from app.models import Thread
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def client(temp_db):
    Base.metadata.create_all(get_engine())
    with TestClient(app) as client:
        yield client


@pytest.fixture
def seeded_thread(client) -> dict:
    """A thread with a company, a contact, two touches, and two stage events."""
    company = client.post("/api/companies", json={"name": "Acme"}).json()
    contact = client.post(
        "/api/contacts", json={"full_name": "Jamie Doe", "company_id": company["id"]}
    ).json()
    thread = client.post(
        "/api/threads", json={"company_id": company["id"], "contact_id": contact["id"]}
    ).json()

    # Touches and stage events are seeded directly through a session — #16/#18
    # (the endpoints that create them) don't exist yet.
    with Session(get_engine()) as session:
        db_thread = session.get(Thread, thread["id"])
        assert db_thread is not None
        from app.models import (
            StageEvent,
            StageOrTerminal,
            Touch,
            TouchChannel,
            TouchDirection,
            TouchKind,
        )

        session.add(
            Touch(
                thread_id=db_thread.id,
                kind=TouchKind.COLD_OUTREACH,
                direction=TouchDirection.OUTBOUND,
                channel=TouchChannel.EMAIL,
                occurred_at=datetime.date(2026, 1, 5),
            )
        )
        session.add(
            Touch(
                thread_id=db_thread.id,
                kind=TouchKind.POST_RECRUITER_CALL,
                direction=TouchDirection.INBOUND,
                channel=TouchChannel.PHONE,
                occurred_at=datetime.date(2026, 1, 1),
            )
        )
        session.add(
            StageEvent(
                thread_id=db_thread.id,
                from_stage=None,
                to_stage=StageOrTerminal.OUTREACH,
                occurred_at=datetime.datetime(2026, 1, 1),
            )
        )
        session.add(
            StageEvent(
                thread_id=db_thread.id,
                from_stage=StageOrTerminal.OUTREACH,
                to_stage=StageOrTerminal.REPLIED,
                occurred_at=datetime.datetime(2026, 1, 5),
            )
        )
        session.commit()

    return thread


def test_detail_includes_company_contact_touches_and_stage_events(client, seeded_thread) -> None:
    response = client.get(f"/api/threads/{seeded_thread['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["company"]["name"] == "Acme"
    assert body["contact"]["full_name"] == "Jamie Doe"

    touches = body["touches"]
    assert len(touches) == 2
    assert touches[0]["occurred_at"] == "2026-01-01"  # ordered ascending
    assert touches[1]["occurred_at"] == "2026-01-05"

    stage_events = body["stage_events"]
    assert len(stage_events) == 2
    assert stage_events[0]["from_stage"] is None
    assert stage_events[1]["from_stage"] == "outreach"


def test_detail_404_for_nonexistent_thread(client) -> None:
    assert client.get("/api/threads/999").status_code == 404


def test_detail_includes_ghost_suggested_and_days_in_stage(client, seeded_thread) -> None:
    response = client.get(f"/api/threads/{seeded_thread['id']}")

    body = response.json()
    assert body["is_ghost_suggested"] is False  # nudge_number is 0
    assert body["days_in_stage"] == 0  # just created


def test_list_includes_ghost_suggested_and_days_in_stage(client, seeded_thread) -> None:
    response = client.get("/api/threads")

    body = response.json()[0]
    assert "is_ghost_suggested" in body
    assert "days_in_stage" in body


def test_list_ghost_suggested_true_once_nudge_reaches_threshold(client) -> None:
    company = client.post("/api/companies", json={"name": "Acme"}).json()
    thread = client.post("/api/threads", json={"company_id": company["id"]}).json()

    with Session(get_engine()) as session:
        db_thread = session.get(Thread, thread["id"])
        assert db_thread is not None
        db_thread.nudge_number = 3
        session.commit()

    response = client.get("/api/threads")
    assert response.json()[0]["is_ghost_suggested"] is True


def test_list_filters_by_status_stage_motion_role_family(client) -> None:
    from app.models import Motion, RoleFamily, Stage, ThreadStatus

    company = client.post("/api/companies", json={"name": "Acme"}).json()
    a = client.post(
        "/api/threads",
        json={
            "company_id": company["id"],
            "role_family": RoleFamily.SWE.value,
            "motion": Motion.COLD_OUTREACH.value,
        },
    ).json()
    b = client.post(
        "/api/threads",
        json={
            "company_id": company["id"],
            "role_family": RoleFamily.MLE.value,
            "motion": Motion.WARM_OUTREACH.value,
        },
    ).json()

    with Session(get_engine()) as session:
        db_b = session.get(Thread, b["id"])
        assert db_b is not None
        db_b.stage = Stage.REPLIED
        db_b.status = ThreadStatus.WITHDRAWN
        session.commit()

    assert {t["id"] for t in client.get("/api/threads").json()} == {a["id"], b["id"]}
    assert [t["id"] for t in client.get("/api/threads", params={"role_family": "SWE"}).json()] == [
        a["id"]
    ]
    assert [
        t["id"] for t in client.get("/api/threads", params={"motion": "cold_outreach"}).json()
    ] == [a["id"]]
    assert [t["id"] for t in client.get("/api/threads", params={"stage": "replied"}).json()] == [
        b["id"]
    ]
    assert [t["id"] for t in client.get("/api/threads", params={"status": "withdrawn"}).json()] == [
        b["id"]
    ]


def test_list_filters_by_company_id(client) -> None:
    company_a = client.post("/api/companies", json={"name": "Acme"}).json()
    company_b = client.post("/api/companies", json={"name": "Zeta"}).json()
    a = client.post("/api/threads", json={"company_id": company_a["id"]}).json()
    client.post("/api/threads", json={"company_id": company_b["id"]})

    response = client.get("/api/threads", params={"company_id": company_a["id"]})

    assert [t["id"] for t in response.json()] == [a["id"]]


def test_read_endpoints_carry_company_and_contact_name(client) -> None:
    company = client.post("/api/companies", json={"name": "Acme"}).json()
    contact = client.post(
        "/api/contacts", json={"full_name": "Jamie Doe", "company_id": company["id"]}
    ).json()
    with_contact = client.post(
        "/api/threads", json={"company_id": company["id"], "contact_id": contact["id"]}
    ).json()
    without_contact = client.post("/api/threads", json={"company_id": company["id"]}).json()

    assert with_contact["company_name"] == "Acme"
    assert with_contact["contact_name"] == "Jamie Doe"
    assert without_contact["company_name"] == "Acme"
    assert without_contact["contact_name"] is None

    listed = {t["id"]: t for t in client.get("/api/threads").json()}
    assert listed[with_contact["id"]]["contact_name"] == "Jamie Doe"
