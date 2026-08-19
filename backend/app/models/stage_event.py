"""The stage_event table (issue #7) — append-only. No update path is added here.

from_stage/to_stage share one enum covering both thread.stage values and
thread's terminal status values, since #18 records transitions to either.
The ERD gives no literal value list for these two columns (unlike every
other enum in the schema) — this is a judgment call, documented in the
groomed issue, not something PLAN.md states outright.
"""

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models._enum import enum_values

if TYPE_CHECKING:
    from app.models.thread import Thread


class StageOrTerminal(StrEnum):
    OUTREACH = "outreach"
    REPLIED = "replied"
    SCREEN = "screen"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    WITHDRAWN = "withdrawn"
    CLOSED = "closed"


class StageEvent(Base):
    __tablename__ = "stage_event"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[int] = mapped_column(
        ForeignKey("thread.id", ondelete="CASCADE"), nullable=False
    )
    from_stage: Mapped[StageOrTerminal | None] = mapped_column(
        Enum(
            StageOrTerminal,
            values_callable=enum_values,
            name="stage_event_from_stage",
            create_constraint=True,
        )
    )
    to_stage: Mapped[StageOrTerminal] = mapped_column(
        Enum(
            StageOrTerminal,
            values_callable=enum_values,
            name="stage_event_to_stage",
            create_constraint=True,
        ),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    thread: Mapped["Thread"] = relationship(back_populates="stage_events")
