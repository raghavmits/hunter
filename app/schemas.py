from datetime import date

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str | None = None
    stage: str | None = None
    interest: str | None = None
    industry: str | None = None
    role: str | None = None
    url: str | None = None
    careers_page: str | None = None
    notes: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    stage: str | None = None
    interest: str | None = None
    industry: str | None = None
    role: str | None = None
    url: str | None = None
    careers_page: str | None = None
    notes: str | None = None


class CompanyRead(BaseModel):
    id: str
    name: str | None
    stage: str | None
    interest: str | None
    industry: str | None
    role: str | None
    url: str | None
    careers_page: str | None
    notes: str | None
    contact_names: list[str]

    model_config = {"from_attributes": True}


class ContactCreate(BaseModel):
    name: str | None = None
    company_id: str | None = None
    title: str | None = None
    contact_mode: str | None = None
    warmth: str | None = None
    last_connected: date | None = None
    next_follow_up: date | None = None
    status: str | None = None
    hiring_companies: str | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    name: str | None = None
    company_id: str | None = None
    title: str | None = None
    contact_mode: str | None = None
    warmth: str | None = None
    last_connected: date | None = None
    next_follow_up: date | None = None
    status: str | None = None
    hiring_companies: str | None = None
    notes: str | None = None


class ContactRead(BaseModel):
    id: str
    name: str | None
    company_id: str | None
    title: str | None
    contact_mode: str | None
    warmth: str | None
    last_connected: date | None
    next_follow_up: date | None
    status: str | None
    hiring_companies: str | None
    notes: str | None

    model_config = {"from_attributes": True}
