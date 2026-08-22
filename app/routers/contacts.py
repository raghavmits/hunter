from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.models.contact import Contact
from app.schemas import ContactCreate, ContactRead, ContactUpdate

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=list[ContactRead])
def list_contacts(session: Session = Depends(get_session)) -> list[Contact]:
    return session.query(Contact).all()


@router.post("/", response_model=ContactRead, status_code=201)
def create_contact(
    body: ContactCreate, session: Session = Depends(get_session)
) -> Contact:
    contact = Contact(**body.model_dump())
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


@router.patch("/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: str, body: ContactUpdate, session: Session = Depends(get_session)
) -> Contact:
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    session.commit()
    session.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: str, session: Session = Depends(get_session)) -> None:
    contact = session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    session.delete(contact)
    session.commit()
