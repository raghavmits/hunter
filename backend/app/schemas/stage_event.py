"""Pydantic read schema for stage_event (issue #15). #18 adds a Create schema later."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import StageOrTerminal


class StageEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    thread_id: int
    from_stage: StageOrTerminal | None
    to_stage: StageOrTerminal
    occurred_at: datetime
    note: str | None
