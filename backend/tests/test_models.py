"""company and contact models (issue #5). Schema built via Base.metadata.create_all()."""

import pytest
from app.db import Base, get_engine
from app.models import Company, CompanyStatus, Contact, ContactWarmth
from sqlalchemy import insert, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@pytest.fixture
def session(temp_db):
    Base.metadata.create_all(get_engine())
    with Session(get_engine()) as session:
        yield session


def test_company_can_be_created_with_only_a_name(session) -> None:
    company = Company(name="Acme")
    session.add(company)
    session.commit()

    session.refresh(company)
    assert company.status == CompanyStatus.WATCHLIST
    assert company.created_at is not None
    assert company.url is None
    assert company.why_interested is None


def test_contact_can_be_created_with_no_company(session) -> None:
    contact = Contact(full_name="Jamie Doe")
    session.add(contact)
    session.commit()

    session.refresh(contact)
    assert contact.company_id is None
    assert contact.company is None


def test_contact_company_relationship_resolves_both_directions(session) -> None:
    company = Company(name="Acme")
    session.add(company)
    session.flush()

    contact = Contact(full_name="Jamie Doe", company_id=company.id)
    session.add(contact)
    session.commit()

    session.refresh(contact)
    session.refresh(company)
    assert contact.company is not None
    assert contact.company.name == "Acme"
    assert company.contacts == [contact]


def test_contact_with_nonexistent_company_id_raises_integrity_error(session) -> None:
    session.add(Contact(full_name="Jamie Doe", company_id=999))

    with pytest.raises(IntegrityError):
        session.commit()


def test_invalid_company_status_raises_integrity_error(session) -> None:
    company = Company(name="Acme")
    session.add(company)
    session.flush()

    with pytest.raises(IntegrityError):
        session.execute(
            update(Company)
            .where(Company.id == company.id)
            .values(status="not-a-real-status")
            .execution_options(synchronize_session=False)
        )


def test_invalid_contact_warmth_raises_integrity_error(session) -> None:
    session.add(Contact(full_name="Jamie Doe"))
    session.flush()

    with pytest.raises(IntegrityError):
        session.execute(
            insert(Contact).values(
                full_name="Bad Row",
                warmth="not-a-real-warmth",
            )
        )


def test_invalid_contact_source_raises_integrity_error(session) -> None:
    with pytest.raises(IntegrityError):
        session.execute(
            insert(Contact).values(
                full_name="Bad Row",
                source="not-a-real-source",
            )
        )


def test_valid_contact_warmth_and_source_round_trip(session) -> None:
    contact = Contact(full_name="Jamie Doe", warmth=ContactWarmth.WARM)
    session.add(contact)
    session.commit()

    session.refresh(contact)
    assert contact.warmth == ContactWarmth.WARM
