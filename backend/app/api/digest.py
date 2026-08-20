"""GET /api/digest (issue #19)."""

from datetime import UTC, date, datetime

from fastapi import APIRouter

from app.cadence import days_in_stage
from app.config import get_config
from app.db import DbSession
from app.digest import DigestRow as DigestRowInternal
from app.digest import build_digest
from app.models import ThreadStatus
from app.repositories import ThreadRepository
from app.schemas.digest import Digest
from app.schemas.digest import DigestRow as DigestRowSchema

router = APIRouter(prefix="/digest", tags=["digest"])


def _to_row(row: DigestRowInternal, now_utc: datetime) -> DigestRowSchema:
    thread = row.thread
    return DigestRowSchema(
        thread_id=thread.id,
        company_id=thread.company_id,
        company_name=thread.company.name,
        contact_id=thread.contact_id,
        contact_name=thread.contact.full_name if thread.contact else None,
        stage=thread.stage,
        days_overdue=row.days_overdue,
        days_in_stage=days_in_stage(thread, now_utc),
    )


@router.get("", response_model=Digest)
def get_digest(db: DbSession) -> Digest:
    open_threads = ThreadRepository(db).list(status=ThreadStatus.OPEN)
    config = get_config()
    now_utc = datetime.now(UTC).replace(tzinfo=None)

    result = build_digest(
        threads=open_threads,
        at_risk_threshold_days=config.at_risk_threshold_days,
        today=date.today(),
        now_utc=now_utc,
    )

    return Digest(
        overdue=[_to_row(r, now_utc) for r in result.overdue],
        due_today=[_to_row(r, now_utc) for r in result.due_today],
        at_risk=[_to_row(r, now_utc) for r in result.at_risk],
        live_conversation_count=result.live_conversation_count,
    )
