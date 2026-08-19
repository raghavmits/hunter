"""Pydantic schemas for /api/companies (issue #12)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import CompanyStatus


class CompanyCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    url: str | None = None
    why_interested: str | None = None
    status: CompanyStatus = CompanyStatus.WATCHLIST


class CompanyUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1)
    url: str | None = None
    why_interested: str | None = None
    status: CompanyStatus | None = None


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str | None
    why_interested: str | None
    status: CompanyStatus
    created_at: datetime
