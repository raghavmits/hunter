"""Pydantic schemas for /api/threads (issue #14)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import Motion, RoleFamily, Stage, ThreadStatus


class ThreadCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company_id: int | None = None
    company_name: str | None = Field(default=None, min_length=1)
    contact_id: int | None = None
    role_title: str | None = None
    role_family: RoleFamily | None = None
    motion: Motion | None = None
    jd_url: str | None = None

    @model_validator(mode="after")
    def _exactly_one_company_field(self) -> "ThreadCreate":
        if (self.company_id is None) == (self.company_name is None):
            raise ValueError("exactly one of company_id or company_name is required")
        return self


class ThreadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    contact_id: int | None
    role_title: str | None
    role_family: RoleFamily | None
    motion: Motion | None
    stage: Stage
    status: ThreadStatus
    stage_entered_at: datetime
    next_follow_up_date: date | None
    nudge_number: int
    follow_up_pinned: bool
    referral_promised: bool
    referral_submitted_at: date | None
    jd_url: str | None
    notes: str | None
    created_at: datetime
    closed_at: datetime | None
