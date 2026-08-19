"""POST /api/threads — quick-add (issue #14)."""

from fastapi import APIRouter, HTTPException

from app.db import DbSession
from app.repositories import CompanyRepository, ContactRepository, ThreadRepository
from app.schemas.thread import ThreadCreate, ThreadRead

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post("", response_model=ThreadRead, status_code=201)
def create_thread(body: ThreadCreate, db: DbSession) -> ThreadRead:
    company_repo = CompanyRepository(db)

    if body.company_id is not None:
        company = company_repo.get(body.company_id)
        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")
    else:
        assert body.company_name is not None  # enforced by ThreadCreate's validator
        company = company_repo.get_by_name(body.company_name)
        if company is None:
            company = company_repo.create(name=body.company_name)

    if body.contact_id is not None and ContactRepository(db).get(body.contact_id) is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    thread = ThreadRepository(db).create(
        company_id=company.id,
        contact_id=body.contact_id,
        role_title=body.role_title,
        role_family=body.role_family,
        motion=body.motion,
        jd_url=body.jd_url,
    )
    db.commit()
    return ThreadRead.model_validate(thread)
