"""Pydantic read schema for touch (issue #15). #16 adds a Create schema later."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models import TouchChannel, TouchDirection, TouchKind


class TouchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    thread_id: int
    kind: TouchKind
    direction: TouchDirection
    channel: TouchChannel
    occurred_at: date
    note: str | None
    created_at: datetime
