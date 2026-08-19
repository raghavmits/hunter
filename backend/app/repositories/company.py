"""Repository for company (issue #8). No session.commit() — callers commit."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, CompanyStatus


class CompanyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: int) -> Company | None:
        return self.session.get(Company, id)

    def get_by_name(self, name: str) -> Company | None:
        return self.session.execute(
            select(Company).where(Company.name == name)
        ).scalar_one_or_none()

    def list(
        self, name_contains: str | None = None, status: CompanyStatus | None = None
    ) -> list[Company]:
        stmt = select(Company)
        if name_contains is not None:
            stmt = stmt.where(Company.name.contains(name_contains))
        if status is not None:
            stmt = stmt.where(Company.status == status)
        return list(self.session.execute(stmt).scalars().all())

    def create(
        self,
        name: str,
        url: str | None = None,
        why_interested: str | None = None,
        status: CompanyStatus = CompanyStatus.WATCHLIST,
    ) -> Company:
        company = Company(name=name, url=url, why_interested=why_interested, status=status)
        self.session.add(company)
        self.session.flush()
        return company

    def update(self, id: int, **fields: object) -> Company | None:
        company = self.get(id)
        if company is None:
            return None
        for key, value in fields.items():
            setattr(company, key, value)
        self.session.flush()
        return company
