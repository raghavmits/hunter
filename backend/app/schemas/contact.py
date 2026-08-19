"""Pydantic schemas for /api/contacts (issue #13).

warmth/source reuse app.models' enums directly rather than re-deriving from
config.yaml — see the groomed issue for why: only `source`'s values come
from config.yaml (contact_sources), warmth never has, and re-deriving
either at the API layer while the DB's CHECK constraint stays fixed to
whatever #5's migration baked in would let the two drift apart silently.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ContactSource, ContactWarmth


class ContactCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=1)
    company_id: int | None = None
    title: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    warmth: ContactWarmth | None = None
    source: ContactSource | None = None
    how_we_met: str | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str | None = Field(default=None, min_length=1)
    company_id: int | None = None
    title: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    warmth: ContactWarmth | None = None
    source: ContactSource | None = None
    how_we_met: str | None = None
    notes: str | None = None


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int | None
    full_name: str
    title: str | None
    email: str | None
    linkedin_url: str | None
    warmth: ContactWarmth | None
    source: ContactSource | None
    how_we_met: str | None
    notes: str | None
    created_at: datetime
