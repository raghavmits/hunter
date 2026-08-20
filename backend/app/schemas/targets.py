"""Pydantic schema for GET /api/targets (issue #21)."""

from pydantic import BaseModel


class TargetProgress(BaseModel):
    count: int
    target: int
    type: str
    deadline: str | None


class TargetsSummary(BaseModel):
    new_connections_made: TargetProgress
    warm_outreach_with_acquaintances: TargetProgress
    cold_applications: TargetProgress
    screens_recruiter_calls: TargetProgress
    interviews: TargetProgress
    offers: TargetProgress
