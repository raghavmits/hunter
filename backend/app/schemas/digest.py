"""Pydantic schemas for GET /api/digest (issue #19).

Company/contact are flattened to id+name, not full nested objects — this is
a list-shaped response (same reasoning #15 used to keep its list endpoint
bare), not a detail view.
"""

from pydantic import BaseModel

from app.models import Stage


class DigestRow(BaseModel):
    thread_id: int
    company_id: int
    company_name: str
    contact_id: int | None
    contact_name: str | None
    stage: Stage
    days_overdue: int | None
    days_in_stage: int


class Digest(BaseModel):
    overdue: list[DigestRow]
    due_today: list[DigestRow]
    at_risk: list[DigestRow]
    live_conversation_count: int
