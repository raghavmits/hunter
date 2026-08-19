"""Repository tests (issue #8) — get/list/create/update against a temp SQLite database."""

import datetime

import pytest
from app.db import Base, get_engine
from app.models import (
    CompanyStatus,
    ContactSource,
    ContactWarmth,
    Motion,
    RoleFamily,
    Stage,
    StageOrTerminal,
    ThreadStatus,
    TouchChannel,
    TouchDirection,
    TouchKind,
)
from app.repositories import (
    CompanyRepository,
    ContactRepository,
    StageEventRepository,
    ThreadRepository,
    TouchRepository,
)
from sqlalchemy.orm import Session


@pytest.fixture
def session(temp_db):
    Base.metadata.create_all(get_engine())
    with Session(get_engine()) as session:
        yield session


# --- CompanyRepository -------------------------------------------------


def test_company_create_get_update(session) -> None:
    repo = CompanyRepository(session)
    company = repo.create(name="Acme", url="https://acme.example")

    assert repo.get(company.id) is company
    assert repo.get(999) is None

    updated = repo.update(company.id, status=CompanyStatus.ACTIVE)
    assert updated is not None
    assert updated.status == CompanyStatus.ACTIVE
    assert repo.update(999, status=CompanyStatus.ACTIVE) is None


def test_company_get_by_name(session) -> None:
    repo = CompanyRepository(session)
    repo.create(name="Acme")

    assert repo.get_by_name("Acme") is not None
    assert repo.get_by_name("Nonexistent") is None


def test_company_list_filters(session) -> None:
    repo = CompanyRepository(session)
    repo.create(name="Acme Corp", status=CompanyStatus.WATCHLIST)
    repo.create(name="Beta Inc", status=CompanyStatus.ACTIVE)

    assert len(repo.list()) == 2
    assert [c.name for c in repo.list(name_contains="Acme")] == ["Acme Corp"]
    assert [c.name for c in repo.list(status=CompanyStatus.ACTIVE)] == ["Beta Inc"]


# --- ContactRepository ---------------------------------------------------


def test_contact_create_get_update(session) -> None:
    repo = ContactRepository(session)
    contact = repo.create(full_name="Jamie Doe", warmth=ContactWarmth.WARM)

    assert repo.get(contact.id) is contact
    assert repo.get(999) is None

    updated = repo.update(contact.id, source=ContactSource.LINKEDIN)
    assert updated is not None
    assert updated.source == ContactSource.LINKEDIN
    assert repo.update(999, source=ContactSource.LINKEDIN) is None


def test_contact_list_by_company(session) -> None:
    company_repo = CompanyRepository(session)
    contact_repo = ContactRepository(session)
    company = company_repo.create(name="Acme")
    contact_repo.create(full_name="With Company", company_id=company.id)
    contact_repo.create(full_name="No Company")

    assert len(contact_repo.list()) == 2
    assert [c.full_name for c in contact_repo.list(company_id=company.id)] == ["With Company"]


# --- ThreadRepository ------------------------------------------------------


def test_thread_create_get_update(session) -> None:
    company = CompanyRepository(session).create(name="Acme")
    repo = ThreadRepository(session)
    thread = repo.create(company_id=company.id, role_title="SWE")

    assert repo.get(thread.id) is thread
    assert repo.get(999) is None

    updated = repo.update(thread.id, nudge_number=1)
    assert updated is not None
    assert updated.nudge_number == 1
    assert repo.update(999, nudge_number=1) is None


def test_thread_list_filters(session) -> None:
    company = CompanyRepository(session).create(name="Acme")
    repo = ThreadRepository(session)
    a = repo.create(company_id=company.id, role_family=RoleFamily.SWE, motion=Motion.COLD_OUTREACH)
    b = repo.create(company_id=company.id, role_family=RoleFamily.MLE, motion=Motion.WARM_OUTREACH)
    repo.update(b.id, stage=Stage.REPLIED, status=ThreadStatus.WITHDRAWN)

    assert {t.id for t in repo.list()} == {a.id, b.id}
    assert [t.id for t in repo.list(role_family=RoleFamily.SWE)] == [a.id]
    assert [t.id for t in repo.list(motion=Motion.COLD_OUTREACH)] == [a.id]
    assert [t.id for t in repo.list(stage=Stage.REPLIED)] == [b.id]
    assert [t.id for t in repo.list(status=ThreadStatus.WITHDRAWN)] == [b.id]


# --- TouchRepository ---------------------------------------------------


def test_touch_repository_has_no_update_method() -> None:
    assert not hasattr(TouchRepository, "update")


def test_touch_create_and_list_for_thread_ordered(session) -> None:
    company = CompanyRepository(session).create(name="Acme")
    thread = ThreadRepository(session).create(company_id=company.id)
    repo = TouchRepository(session)

    repo.create(
        thread_id=thread.id,
        kind=TouchKind.COLD_OUTREACH,
        direction=TouchDirection.OUTBOUND,
        channel=TouchChannel.EMAIL,
        occurred_at=datetime.date(2026, 1, 5),
    )
    repo.create(
        thread_id=thread.id,
        kind=TouchKind.POST_RECRUITER_CALL,
        direction=TouchDirection.INBOUND,
        channel=TouchChannel.PHONE,
        occurred_at=datetime.date(2026, 1, 1),
    )

    touches = repo.list_for_thread(thread.id)
    assert [t.occurred_at for t in touches] == [
        datetime.date(2026, 1, 1),
        datetime.date(2026, 1, 5),
    ]
    assert repo.list_for_thread(999) == []


# --- StageEventRepository ------------------------------------------------


def test_stage_event_repository_has_no_update_method() -> None:
    assert not hasattr(StageEventRepository, "update")


def test_stage_event_create_and_list_for_thread_ordered(session) -> None:
    company = CompanyRepository(session).create(name="Acme")
    thread = ThreadRepository(session).create(company_id=company.id)
    repo = StageEventRepository(session)

    repo.create(
        thread_id=thread.id,
        from_stage=StageOrTerminal.OUTREACH,
        to_stage=StageOrTerminal.REPLIED,
        occurred_at=datetime.datetime(2026, 1, 5),
    )
    repo.create(
        thread_id=thread.id,
        from_stage=None,
        to_stage=StageOrTerminal.OUTREACH,
        occurred_at=datetime.datetime(2026, 1, 1),
    )

    events = repo.list_for_thread(thread.id)
    assert [e.to_stage for e in events] == [StageOrTerminal.OUTREACH, StageOrTerminal.REPLIED]
    assert repo.list_for_thread(999) == []
