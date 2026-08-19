"""The company table (issue #5)."""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base
from app.models._enum import enum_values

if TYPE_CHECKING:
    from app.models.contact import Contact


class CompanyStatus(StrEnum):
    WATCHLIST = "watchlist"
    ACTIVE = "active"
    DORMANT = "dormant"
    CLOSED = "closed"


class Company(Base):
    __tablename__ = "company"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str | None] = mapped_column(String)
    why_interested: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CompanyStatus] = mapped_column(
        Enum(
            CompanyStatus,
            values_callable=enum_values,
            name="company_status",
            create_constraint=True,
        ),
        nullable=False,
        default=CompanyStatus.WATCHLIST,
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    contacts: Mapped[list["Contact"]] = relationship(back_populates="company")
