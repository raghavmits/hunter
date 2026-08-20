"""Pydantic schema for GET /api/funnel (issue #22)."""

from pydantic import BaseModel

from app.models import Stage


class FunnelStage(BaseModel):
    stage: Stage
    count: int
    conversion_from_previous: float | None


class Funnel(BaseModel):
    stages: list[FunnelStage]
