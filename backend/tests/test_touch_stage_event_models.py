"""touch and stage_event models (issue #7) — append-only history, cascade on thread delete."""

import datetime

import pytest
from app.db import Base, get_engine
from app.models import (
    Company,
    StageEvent,
    StageOrTerminal,
    Thread,
    Touch,
    TouchChannel,
    TouchDirection,
    TouchKind,
)
from sqlalchemy import insert, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@pytest.fixture
def session(temp_db):
    Base.metadata.create_all(get_engine())
    with Session(get_engine()) as session:
        yield session


@pytest.fixture
def thread(session):
    company = Company(name="Acme")
    session.add(company)
    session.flush()
    thread = Thread(company_id=company.id)
    session.add(thread)
    session.flush()
    return thread


def test_touch_can_be_inserted_and_read_back(session, thread) -> None:
    touch = Touch(
        thread_id=thread.id,
        kind=TouchKind.COLD_OUTREACH,
        direction=TouchDirection.OUTBOUND,
        channel=TouchChannel.EMAIL,
        occurred_at=datetime.date(2026, 1, 1),
        note="first touch",
    )
    session.add(touch)
    session.commit()

    session.refresh(touch)
    assert touch.kind == TouchKind.COLD_OUTREACH
    assert touch.direction == TouchDirection.OUTBOUND
    assert touch.channel == TouchChannel.EMAIL
    assert touch.occurred_at == datetime.date(2026, 1, 1)
    assert touch.note == "first touch"
    assert touch.created_at is not None


def test_first_stage_event_has_null_from_stage(session, thread) -> None:
    event = StageEvent(
        thread_id=thread.id,
        from_stage=None,
        to_stage=StageOrTerminal.OUTREACH,
        occurred_at=datetime.datetime(2026, 1, 1),
    )
    session.add(event)
    session.commit()

    session.refresh(event)
    assert event.from_stage is None
    assert event.to_stage == StageOrTerminal.OUTREACH


def test_second_stage_event_has_a_from_stage(session, thread) -> None:
    first = StageEvent(
        thread_id=thread.id,
        from_stage=None,
        to_stage=StageOrTerminal.OUTREACH,
        occurred_at=datetime.datetime(2026, 1, 1),
    )
    session.add(first)
    session.flush()

    second = StageEvent(
        thread_id=thread.id,
        from_stage=StageOrTerminal.OUTREACH,
        to_stage=StageOrTerminal.REPLIED,
        occurred_at=datetime.datetime(2026, 1, 2),
    )
    session.add(second)
    session.commit()

    session.refresh(second)
    assert second.from_stage == StageOrTerminal.OUTREACH
    assert second.to_stage == StageOrTerminal.REPLIED


@pytest.mark.parametrize(
    ("column", "value"),
    [("kind", "bogus"), ("direction", "bogus"), ("channel", "bogus")],
)
def test_invalid_touch_enum_raises_integrity_error(session, thread, column, value) -> None:
    valid = {
        "kind": TouchKind.COLD_OUTREACH,
        "direction": TouchDirection.OUTBOUND,
        "channel": TouchChannel.EMAIL,
        "occurred_at": datetime.date(2026, 1, 1),
    }
    valid[column] = value

    with pytest.raises(IntegrityError):
        session.execute(insert(Touch).values(thread_id=thread.id, **valid))


@pytest.mark.parametrize("column", ["from_stage", "to_stage"])
def test_invalid_stage_event_enum_raises_integrity_error(session, thread, column) -> None:
    valid = {
        "from_stage": None,
        "to_stage": StageOrTerminal.OUTREACH,
        "occurred_at": datetime.datetime(2026, 1, 1),
    }
    valid[column] = "bogus"

    with pytest.raises(IntegrityError):
        session.execute(insert(StageEvent).values(thread_id=thread.id, **valid))


def test_deleting_a_thread_cascades_to_touch_and_stage_event(session, thread) -> None:
    session.add(
        Touch(
            thread_id=thread.id,
            kind=TouchKind.COLD_OUTREACH,
            direction=TouchDirection.OUTBOUND,
            channel=TouchChannel.EMAIL,
            occurred_at=datetime.date(2026, 1, 1),
        )
    )
    session.add(
        StageEvent(
            thread_id=thread.id,
            from_stage=None,
            to_stage=StageOrTerminal.OUTREACH,
            occurred_at=datetime.datetime(2026, 1, 1),
        )
    )
    session.commit()

    session.delete(thread)
    session.commit()

    assert session.query(Touch).count() == 0
    assert session.query(StageEvent).count() == 0


def test_cascade_holds_at_the_database_level_not_just_via_the_orm(session, thread) -> None:
    """session.delete() would cascade via SQLAlchemy's own relationship
    cascade regardless of the database. Delete with raw SQL, bypassing the
    ORM entirely, to prove ON DELETE CASCADE is doing the work."""
    session.add(
        Touch(
            thread_id=thread.id,
            kind=TouchKind.COLD_OUTREACH,
            direction=TouchDirection.OUTBOUND,
            channel=TouchChannel.EMAIL,
            occurred_at=datetime.date(2026, 1, 1),
        )
    )
    session.add(
        StageEvent(
            thread_id=thread.id,
            from_stage=None,
            to_stage=StageOrTerminal.OUTREACH,
            occurred_at=datetime.datetime(2026, 1, 1),
        )
    )
    session.commit()

    with get_engine().connect() as conn:
        conn.execute(text("DELETE FROM thread WHERE id = :id"), {"id": thread.id})
        conn.commit()

    with get_engine().connect() as conn:
        touch_count = conn.execute(text("SELECT COUNT(*) FROM touch")).scalar()
        stage_event_count = conn.execute(text("SELECT COUNT(*) FROM stage_event")).scalar()
    assert touch_count == 0
    assert stage_event_count == 0
