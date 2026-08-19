"""GET/POST/PATCH /api/companies (issue #12)."""

from fastapi import APIRouter, HTTPException

from app.db import DbSession
from app.models import CompanyStatus
from app.repositories import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyRead, status_code=201)
def create_company(body: CompanyCreate, db: DbSession) -> CompanyRead:
    company = CompanyRepository(db).create(
        name=body.name, url=body.url, why_interested=body.why_interested, status=body.status
    )
    db.commit()
    return CompanyRead.model_validate(company)


@router.get("", response_model=list[CompanyRead])
def list_companies(
    db: DbSession,
    name: str | None = None,
    status: CompanyStatus | None = None,
) -> list[CompanyRead]:
    companies = CompanyRepository(db).list(name_contains=name, status=status)
    return [CompanyRead.model_validate(c) for c in companies]


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: DbSession) -> CompanyRead:
    company = CompanyRepository(db).get(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyRead.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, body: CompanyUpdate, db: DbSession) -> CompanyRead:
    fields = body.model_dump(exclude_unset=True)
    company = CompanyRepository(db).update(company_id, **fields)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    db.commit()
    return CompanyRead.model_validate(company)
