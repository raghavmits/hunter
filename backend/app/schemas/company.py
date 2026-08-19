"""Pydantic schemas for /api/companies (issue #12)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import CompanyStatus


class CompanyCreate(BaseModel):
    name: str
    url: str | None = None
    why_interested: str | None = None
    status: CompanyStatus = CompanyStatus.WATCHLIST


class CompanyUpdate(BaseModel):
    name: str | None = None
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
