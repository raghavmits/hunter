"""GET /api/digest (issue #19)."""

import datetime

import pytest
from app.db import Base, get_engine
from app.main import app
from app.models import Stage, Thread, ThreadStatus
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

TODAY = datetime.date.today()
NOW_UTC = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


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


def _set(thread_id: int, **fields) -> None:
    with Session(get_engine()) as session:
        thread = session.get(Thread, thread_id)
        assert thread is not None
        for key, value in fields.items():
            setattr(thread, key, value)
        session.commit()


def test_digest_partitions_seeded_threads_correctly(client, company_id) -> None:
    overdue_id = _new_thread(client, company_id)
    due_today_id = _new_thread(client, company_id)
    future_id = _new_thread(client, company_id)
    at_risk_id = _new_thread(client, company_id)
    closed_id = _new_thread(client, company_id)

    _set(overdue_id, next_follow_up_date=TODAY - datetime.timedelta(days=3), stage=Stage.REPLIED)
    _set(due_today_id, next_follow_up_date=TODAY)
    _set(future_id, next_follow_up_date=TODAY + datetime.timedelta(days=3))
    _set(at_risk_id, stage_entered_at=NOW_UTC - datetime.timedelta(days=10))
    _set(
        closed_id,
        status=ThreadStatus.REJECTED,
        next_follow_up_date=TODAY - datetime.timedelta(days=5),
        stage_entered_at=NOW_UTC - datetime.timedelta(days=10),
    )

    digest = client.get("/api/digest").json()

    assert [row["thread_id"] for row in digest["overdue"]] == [overdue_id]
    assert [row["thread_id"] for row in digest["due_today"]] == [due_today_id]
    assert [row["thread_id"] for row in digest["at_risk"]] == [at_risk_id]
    # future_id and closed_id appear in none of the lists
    all_ids = {
        row["thread_id"]
        for group in (digest["overdue"], digest["due_today"], digest["at_risk"])
        for row in group
    }
    assert future_id not in all_ids
    assert closed_id not in all_ids


def test_closed_thread_excluded_even_when_it_would_otherwise_qualify(client, company_id) -> None:
    thread_id = _new_thread(client, company_id)
    _set(
        thread_id,
        status=ThreadStatus.GHOSTED,
        next_follow_up_date=TODAY - datetime.timedelta(days=10),
        stage=Stage.REPLIED,
        stage_entered_at=NOW_UTC - datetime.timedelta(days=20),
    )

    digest = client.get("/api/digest").json()

    assert digest["overdue"] == []
    assert digest["at_risk"] == []
    assert digest["live_conversation_count"] == 0


def test_thread_can_be_both_overdue_and_at_risk(client, company_id) -> None:
    thread_id = _new_thread(client, company_id)
    _set(
        thread_id,
        next_follow_up_date=TODAY - datetime.timedelta(days=1),
        stage_entered_at=NOW_UTC - datetime.timedelta(days=10),
    )

    digest = client.get("/api/digest").json()

    assert [row["thread_id"] for row in digest["overdue"]] == [thread_id]
    assert [row["thread_id"] for row in digest["at_risk"]] == [thread_id]


def test_overdue_sorted_by_days_overdue_descending(client, company_id) -> None:
    less_overdue = _new_thread(client, company_id)
    more_overdue = _new_thread(client, company_id)
    _set(less_overdue, next_follow_up_date=TODAY - datetime.timedelta(days=1))
    _set(more_overdue, next_follow_up_date=TODAY - datetime.timedelta(days=5))

    digest = client.get("/api/digest").json()

    assert [row["thread_id"] for row in digest["overdue"]] == [more_overdue, less_overdue]


def test_live_conversation_count_excludes_outreach_stage(client, company_id) -> None:
    outreach_thread = _new_thread(client, company_id)  # stays at default stage=outreach
    replied_thread = _new_thread(client, company_id)
    _set(replied_thread, stage=Stage.REPLIED)

    digest = client.get("/api/digest").json()

    assert digest["live_conversation_count"] == 1
    assert outreach_thread  # created but not counted


def test_open_thread_with_no_follow_up_date_can_still_be_at_risk(client, company_id) -> None:
    thread_id = _new_thread(client, company_id)
    _set(thread_id, stage_entered_at=NOW_UTC - datetime.timedelta(days=10))

    digest = client.get("/api/digest").json()

    assert [row["thread_id"] for row in digest["overdue"]] == []
    assert [row["thread_id"] for row in digest["due_today"]] == []
    assert [row["thread_id"] for row in digest["at_risk"]] == [thread_id]


def test_digest_row_carries_company_and_contact_names(client, company_id) -> None:
    contact = client.post(
        "/api/contacts", json={"full_name": "Jamie Doe", "company_id": company_id}
    ).json()
    thread_id = client.post(
        "/api/threads", json={"company_id": company_id, "contact_id": contact["id"]}
    ).json()["id"]
    _set(thread_id, next_follow_up_date=TODAY)

    digest = client.get("/api/digest").json()

    row = digest["due_today"][0]
    assert row["company_name"] == "Acme"
    assert row["contact_name"] == "Jamie Doe"


def test_digest_row_carries_ghost_suggestion_state(client, company_id) -> None:
    below_threshold_id = _new_thread(client, company_id)
    at_threshold_id = _new_thread(client, company_id)
    _set(below_threshold_id, next_follow_up_date=TODAY, nudge_number=2)
    _set(at_threshold_id, next_follow_up_date=TODAY, nudge_number=3)

    digest = client.get("/api/digest").json()
    rows = {row["thread_id"]: row for row in digest["due_today"]}

    assert rows[below_threshold_id]["nudge_number"] == 2
    assert rows[below_threshold_id]["is_ghost_suggested"] is False
    assert rows[at_threshold_id]["nudge_number"] == 3
    assert rows[at_threshold_id]["is_ghost_suggested"] is True
