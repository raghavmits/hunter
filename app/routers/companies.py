from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.models.company import Company
from app.models.contact import Contact
from app.schemas import CompanyCreate, CompanyRead, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


def _to_read(company: Company, session: Session) -> CompanyRead:
    contact_names = [
        c.name or ""
        for c in session.query(Contact).filter(Contact.company_id == company.id).all()
    ]
    return CompanyRead(
        id=company.id,
        name=company.name,
        stage=company.stage,
        interest=company.interest,
        industry=company.industry,
        role=company.role,
        url=company.url,
        careers_page=company.careers_page,
        notes=company.notes,
        contact_names=contact_names,
    )


@router.get("/", response_model=list[CompanyRead])
def list_companies(session: Session = Depends(get_session)) -> list[CompanyRead]:
    companies = session.query(Company).all()
    return [_to_read(c, session) for c in companies]


@router.post("/", response_model=CompanyRead, status_code=201)
def create_company(
    body: CompanyCreate, session: Session = Depends(get_session)
) -> CompanyRead:
    company = Company(**body.model_dump())
    session.add(company)
    session.commit()
    session.refresh(company)
    return _to_read(company, session)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: str, body: CompanyUpdate, session: Session = Depends(get_session)
) -> CompanyRead:
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    session.commit()
    session.refresh(company)
    return _to_read(company, session)


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: str, session: Session = Depends(get_session)) -> None:
    company = session.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # Nullify company_id on linked contacts (mirrors HTML behaviour)
    session.query(Contact).filter(Contact.company_id == company_id).update(
        {Contact.company_id: None}
    )
    session.delete(company)
    session.commit()
