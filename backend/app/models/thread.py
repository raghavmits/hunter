"""The thread table (issue #6) — the central pursuit record.

role_family and motion are nullable: FR-4 lists both as optional on
quick-add, even though the ERD doesn't annotate them "nullable" the way it
does contact_id.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base
from app.models._enum import enum_values

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.contact import Contact
    from app.models.stage_event import StageEvent
    from app.models.touch import Touch


class RoleFamily(StrEnum):
    FDE = "FDE"
    SWE = "SWE"
    MLE = "MLE"
    MTS = "MTS"
    OTHER = "OTHER"


class Motion(StrEnum):
    COLD_OUTREACH = "cold_outreach"
    WARM_OUTREACH = "warm_outreach"
    COLD_APPLICATION = "cold_application"


class Stage(StrEnum):
    OUTREACH = "outreach"
    REPLIED = "replied"
    SCREEN = "screen"
    INTERVIEW = "interview"
    OFFER = "offer"


class ThreadStatus(StrEnum):
    OPEN = "open"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    WITHDRAWN = "withdrawn"
    CLOSED = "closed"


class Thread(Base):
    __tablename__ = "thread"
    __table_args__ = (
        Index("ix_thread_status_next_follow_up_date", "status", "next_follow_up_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id"), nullable=False)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contact.id"))
    role_title: Mapped[str | None] = mapped_column(String)
    role_family: Mapped[RoleFamily | None] = mapped_column(
        Enum(
            RoleFamily,
            values_callable=enum_values,
            name="thread_role_family",
            create_constraint=True,
        )
    )
    motion: Mapped[Motion | None] = mapped_column(
        Enum(Motion, values_callable=enum_values, name="thread_motion", create_constraint=True)
    )
    stage: Mapped[Stage] = mapped_column(
        Enum(Stage, values_callable=enum_values, name="thread_stage", create_constraint=True),
        nullable=False,
        default=Stage.OUTREACH,
    )
    status: Mapped[ThreadStatus] = mapped_column(
        Enum(
            ThreadStatus, values_callable=enum_values, name="thread_status", create_constraint=True
        ),
        nullable=False,
        default=ThreadStatus.OPEN,
    )
    stage_entered_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    next_follow_up_date: Mapped[date | None] = mapped_column()
    nudge_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    follow_up_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    referral_promised: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    referral_submitted_at: Mapped[date | None] = mapped_column()
    jd_url: Mapped[str | None] = mapped_column(String)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    closed_at: Mapped[datetime | None] = mapped_column()

    company: Mapped["Company"] = relationship()
    contact: Mapped["Contact | None"] = relationship()
    touches: Mapped[list["Touch"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )
    stage_events: Mapped[list["StageEvent"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )
