"""The thread model (issue #6)."""

import pytest
from app.db import Base, get_engine
from app.models import Company, Contact, Stage, Thread, ThreadStatus
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@pytest.fixture
def session(temp_db):
    Base.metadata.create_all(get_engine())
    with Session(get_engine()) as session:
        yield session


@pytest.fixture
def company(session):
    company = Company(name="Acme")
    session.add(company)
    session.flush()
    return company


def test_thread_can_be_created_with_only_a_company(session, company) -> None:
    thread = Thread(company_id=company.id)
    session.add(thread)
    session.commit()

    session.refresh(thread)
    assert thread.contact_id is None
    assert thread.role_title is None
    assert thread.role_family is None
    assert thread.motion is None
    assert thread.next_follow_up_date is None
    assert thread.referral_submitted_at is None
    assert thread.jd_url is None
    assert thread.closed_at is None


def test_defaults_on_a_freshly_created_thread(session, company) -> None:
    thread = Thread(company_id=company.id)
    session.add(thread)
    session.commit()

    session.refresh(thread)
    assert thread.stage == Stage.OUTREACH
    assert thread.status == ThreadStatus.OPEN
    assert thread.nudge_number == 0
    assert thread.follow_up_pinned is False
    assert thread.referral_promised is False
    assert thread.stage_entered_at is not None
    assert thread.created_at is not None


def test_thread_can_be_created_with_a_contact(session, company) -> None:
    contact = Contact(full_name="Jamie Doe", company_id=company.id)
    session.add(contact)
    session.flush()

    thread = Thread(company_id=company.id, contact_id=contact.id)
    session.add(thread)
    session.commit()

    session.refresh(thread)
    assert thread.contact_id == contact.id


def test_thread_with_nonexistent_company_raises_integrity_error(session) -> None:
    session.add(Thread(company_id=999))

    with pytest.raises(IntegrityError):
        session.commit()


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("role_family", "not-a-real-family"),
        ("motion", "not-a-real-motion"),
        ("stage", "not-a-real-stage"),
        ("status", "not-a-real-status"),
    ],
)
def test_invalid_enum_value_raises_integrity_error(session, company, column, value) -> None:
    with pytest.raises(IntegrityError):
        session.execute(insert(Thread).values(company_id=company.id, **{column: value}))


def test_composite_index_exists_on_status_and_next_follow_up_date() -> None:
    table = Base.metadata.tables["thread"]
    index_names = {index.name for index in table.indexes}
    assert "ix_thread_status_next_follow_up_date" in index_names

    (index,) = [i for i in table.indexes if i.name == "ix_thread_status_next_follow_up_date"]
    assert [c.name for c in index.columns] == ["status", "next_follow_up_date"]
