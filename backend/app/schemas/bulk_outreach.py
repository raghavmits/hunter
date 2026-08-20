"""Pydantic schemas for POST /api/threads/bulk-outreach (issue #34).

company_name and contact_id are deliberately unconstrained at the schema
level (no min_length, no existence check) — those are runtime, per-row
checks in the endpoint, not request-level validation. A schema-level
constraint would reject the whole batch on one bad row, which is exactly
what #34's per-row failure reporting is designed to avoid.
"""

from datetime import date

from pydantic import BaseModel, Field

from app.models import TouchChannel, TouchKind


class BulkOutreachRow(BaseModel):
    company_name: str
    contact_id: int | None = None
    role_title: str | None = None


class BulkOutreachRequest(BaseModel):
    kind: TouchKind
    channel: TouchChannel
    occurred_at: date | None = None
    rows: list[BulkOutreachRow] = Field(min_length=1)


class BulkOutreachRowResult(BaseModel):
    row_index: int
    success: bool
    error: str | None = None
    thread_id: int | None = None


class BulkOutreachResult(BaseModel):
    results: list[BulkOutreachRowResult]
