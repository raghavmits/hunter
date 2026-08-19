"""POST /api/threads/{id}/touches (issue #16)."""

import datetime

import pytest
from app.business_days import add_business_days
from app.config import get_config
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
def thread_id(client) -> int:
    company = client.post("/api/companies", json={"name": "Acme"}).json()
    return client.post("/api/threads", json={"company_id": company["id"]}).json()["id"]


def _set_thread(thread_id: int, **fields) -> None:
    with Session(get_engine()) as session:
        thread = session.get(Thread, thread_id)
        assert thread is not None
        for key, value in fields.items():
            setattr(thread, key, value)
        session.commit()


def test_outbound_touch_sets_the_expected_date(client, thread_id) -> None:
    response = client.post(
        f"/api/threads/{thread_id}/touches",
        json={"kind": "cold_outreach", "direction": "outbound", "channel": "email"},
    )

    assert response.status_code == 201
    body = response.json()
    expected = add_business_days(datetime.date.today(), 5)  # cold_outreach's 1st nudge
    assert body["thread"]["next_follow_up_date"] == expected.isoformat()
    assert body["thread"]["nudge_number"] == 1
    assert body["touch"]["kind"] == "cold_outreach"
    assert body["touch"]["direction"] == "outbound"


def test_inbound_touch_clears_the_date(client, thread_id) -> None:
    client.post(
        f"/api/threads/{thread_id}/touches",
        json={"kind": "cold_outreach", "direction": "outbound", "channel": "email"},
    )

    response = client.post(
        f"/api/threads/{thread_id}/touches",
        json={"kind": "cold_outreach", "direction": "inbound", "channel": "email"},
    )

    body = response.json()
    assert body["thread"]["next_follow_up_date"] is None
    assert body["thread"]["nudge_number"] == 0


def test_pinned_thread_outbound_touch_leaves_the_date_untouched(client, thread_id) -> None:
    # A real, non-null pre-existing date — this is what actually exercises the
    # should_update_date=False path. A null date beforehand would make "untouched"
    # and "cleared" look identical.
    pinned_date = datetime.date(2030, 6, 15)
    _set_thread(thread_id, follow_up_pinned=True, next_follow_up_date=pinned_date, nudge_number=1)

    response = client.post(
        f"/api/threads/{thread_id}/touches",
        json={"kind": "cold_outreach", "direction": "outbound", "channel": "email"},
    )

    body = response.json()
    assert body["thread"]["next_follow_up_date"] == pinned_date.isoformat()
    assert body["thread"]["nudge_number"] == 2  # nudge still advances


def test_pinned_thread_inbound_touch_leaves_the_date_untouched(client, thread_id) -> None:
    pinned_date = datetime.date(2030, 6, 15)
    _set_thread(thread_id, follow_up_pinned=True, next_follow_up_date=pinned_date, nudge_number=2)

    response = client.post(
        f"/api/threads/{thread_id}/touches",
        json={"kind": "cold_outreach", "direction": "inbound", "channel": "email"},
    )

    body = response.json()
    assert body["thread"]["next_follow_up_date"] == pinned_date.isoformat()
    assert body["thread"]["nudge_number"] == 0  # nudge still resets


def test_occurred_at_defaults_to_today(client, thread_id) -> None:
    response = client.post(
        f"/api/threads/{thread_id}/touches",
        json={"kind": "cold_outreach", "direction": "outbound", "channel": "email"},
    )

    assert response.json()["touch"]["occurred_at"] == datetime.date.today().isoformat()


def test_logged_touch_appears_in_thread_detail(client, thread_id) -> None:
    client.post(
        f"/api/threads/{thread_id}/touches",
        json={
            "kind": "cold_outreach",
            "direction": "outbound",
            "channel": "email",
            "note": "first outreach",
        },
    )

    detail = client.get(f"/api/threads/{thread_id}").json()
    assert len(detail["touches"]) == 1
    assert detail["touches"][0]["note"] == "first outreach"


def test_log_touch_on_nonexistent_thread_is_404(client) -> None:
    response = client.post(
        "/api/threads/999/touches",
        json={"kind": "cold_outreach", "direction": "outbound", "channel": "email"},
    )
    assert response.status_code == 404


def test_config_cadence_key_matches_touch_kind() -> None:
    # Sanity check the fixture data below matches the real config, so the
    # exact-date assertion above isn't quietly testing stale expectations.
    assert get_config().cadence["cold_outreach"].intervals[0] == 5
