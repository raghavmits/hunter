"""The contact table (issue #5). company_id is nullable — the bottom-up
sheet is full of people with no company."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base
from app.models._enum import enum_values

if TYPE_CHECKING:
    from app.models.company import Company


class ContactWarmth(StrEnum):
    COLD = "cold"
    WARM = "warm"
    STRONG = "strong"


class ContactSource(StrEnum):
    RECRUITER = "recruiter"
    ENG_MANAGER = "eng_manager"
    FRIEND = "friend"
    FAMILY = "family"
    EX_COLLEAGUE = "ex_colleague"
    LINKEDIN = "linkedin"
    BERKELEY_IITK = "berkeley_iitk"
    NETWORKING_EVENT = "networking_event"
    HACKATHON = "hackathon"
    INTERVIEWED_AT = "interviewed_at"
    FRIEND_OF_FRIEND = "friend_of_friend"


class Contact(Base):
    __tablename__ = "contact"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("company.id"))
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    linkedin_url: Mapped[str | None] = mapped_column(String)
    warmth: Mapped[ContactWarmth | None] = mapped_column(
        Enum(
            ContactWarmth,
            values_callable=enum_values,
            name="contact_warmth",
            create_constraint=True,
        )
    )
    source: Mapped[ContactSource | None] = mapped_column(
        Enum(
            ContactSource,
            values_callable=enum_values,
            name="contact_source",
            create_constraint=True,
        )
    )
    how_we_met: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    company: Mapped["Company | None"] = relationship(back_populates="contacts")
