"""Pydantic schemas for stage_event (issues #15, #18)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import StageOrTerminal


class StageChange(BaseModel):
    """Issue #18. `to` is either one of the five stage values or one of the
    four terminal status values — the same nine-value union #7 already
    defined for stage_event.from_stage/to_stage."""

    to: StageOrTerminal
    note: str | None = None


class StageEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    thread_id: int
    from_stage: StageOrTerminal | None
    to_stage: StageOrTerminal
    occurred_at: datetime
    note: str | None
