"""GET/POST/PATCH /api/contacts (issue #13)."""

from fastapi import APIRouter, HTTPException

from app.db import DbSession
from app.repositories import CompanyRepository, ContactRepository
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _check_company_exists(db: DbSession, company_id: int | None) -> None:
    if company_id is not None and CompanyRepository(db).get(company_id) is None:
        raise HTTPException(status_code=404, detail="Company not found")


@router.post("", response_model=ContactRead, status_code=201)
def create_contact(body: ContactCreate, db: DbSession) -> ContactRead:
    _check_company_exists(db, body.company_id)
    contact = ContactRepository(db).create(**body.model_dump())
    db.commit()
    return ContactRead.model_validate(contact)


@router.get("", response_model=list[ContactRead])
def list_contacts(db: DbSession, company_id: int | None = None) -> list[ContactRead]:
    contacts = ContactRepository(db).list(company_id=company_id)
    return [ContactRead.model_validate(c) for c in contacts]


@router.get("/{contact_id}", response_model=ContactRead)
def get_contact(contact_id: int, db: DbSession) -> ContactRead:
    contact = ContactRepository(db).get(contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return ContactRead.model_validate(contact)


@router.patch("/{contact_id}", response_model=ContactRead)
def update_contact(contact_id: int, body: ContactUpdate, db: DbSession) -> ContactRead:
    fields = body.model_dump(exclude_unset=True)
    if "company_id" in fields:
        _check_company_exists(db, fields["company_id"])
    contact = ContactRepository(db).update(contact_id, **fields)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.commit()
    return ContactRead.model_validate(contact)
