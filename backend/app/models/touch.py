"""The touch table (issue #7) — append-only. No update path is added here."""

from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base
from app.models._enum import enum_values

if TYPE_CHECKING:
    from app.models.thread import Thread


class TouchKind(StrEnum):
    """The seven cadence keys from config.yaml (#3) — what #10's cadence engine looks up by."""

    COLD_OUTREACH = "cold_outreach"
    WARM_INTRO_REQUEST = "warm_intro_request"
    REFERRAL_PROMISED = "referral_promised"
    POST_RECRUITER_CALL = "post_recruiter_call"
    POST_INTERVIEW = "post_interview"
    APPLICATION_SUBMITTED = "application_submitted"
    LONG_TERM_NURTURE = "long_term_nurture"


class TouchDirection(StrEnum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class TouchChannel(StrEnum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    REFERRAL = "referral"
    PHONE = "phone"
    IN_PERSON = "in_person"
    PORTAL = "portal"
    OTHER = "other"


class Touch(Base):
    __tablename__ = "touch"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(
        ForeignKey("thread.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[TouchKind] = mapped_column(
        Enum(TouchKind, values_callable=enum_values, name="touch_kind", create_constraint=True),
        nullable=False,
    )
    direction: Mapped[TouchDirection] = mapped_column(
        Enum(
            TouchDirection,
            values_callable=enum_values,
            name="touch_direction",
            create_constraint=True,
        ),
        nullable=False,
    )
    channel: Mapped[TouchChannel] = mapped_column(
        Enum(
            TouchChannel, values_callable=enum_values, name="touch_channel", create_constraint=True
        ),
        nullable=False,
    )
    occurred_at: Mapped[date] = mapped_column(nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    thread: Mapped["Thread"] = relationship(back_populates="touches")
