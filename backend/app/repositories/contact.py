"""Repository for contact (issue #8). No session.commit() — callers commit."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contact, ContactSource, ContactWarmth


class ContactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: int) -> Contact | None:
        return self.session.get(Contact, id)

    def list(self, company_id: int | None = None) -> list[Contact]:
        stmt = select(Contact)
        if company_id is not None:
            stmt = stmt.where(Contact.company_id == company_id)
        return list(self.session.execute(stmt).scalars().all())

    def create(
        self,
        full_name: str,
        company_id: int | None = None,
        title: str | None = None,
        email: str | None = None,
        linkedin_url: str | None = None,
        warmth: ContactWarmth | None = None,
        source: ContactSource | None = None,
        how_we_met: str | None = None,
        notes: str | None = None,
    ) -> Contact:
        contact = Contact(
            full_name=full_name,
            company_id=company_id,
            title=title,
            email=email,
            linkedin_url=linkedin_url,
            warmth=warmth,
            source=source,
            how_we_met=how_we_met,
            notes=notes,
        )
        self.session.add(contact)
        self.session.flush()
        return contact

    def update(self, id: int, **fields: object) -> Contact | None:
        contact = self.get(id)
        if contact is None:
            return None
        for key, value in fields.items():
            setattr(contact, key, value)
        self.session.flush()
        return contact
