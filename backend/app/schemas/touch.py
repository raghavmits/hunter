"""Pydantic schemas for touch (issues #15, #16)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models import TouchChannel, TouchDirection, TouchKind


class TouchCreate(BaseModel):
    kind: TouchKind
    direction: TouchDirection
    channel: TouchChannel
    occurred_at: date | None = None  # defaults to today (local — see #16's groomed issue)
    note: str | None = None


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
