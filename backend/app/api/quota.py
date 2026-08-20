"""GET /api/quotas (issue #20)."""

from datetime import date

from fastapi import APIRouter

from app.config import get_config
from app.db import DbSession
from app.quota import build_quota_progress
from app.repositories import TouchRepository
from app.schemas.quota import QuotaSummary

router = APIRouter(prefix="/quotas", tags=["quotas"])


@router.get("", response_model=QuotaSummary)
def get_quota_progress(db: DbSession) -> QuotaSummary:
    touches_today = TouchRepository(db).list_by_occurred_at(date.today())
    progress = build_quota_progress(touches_today, get_config().daily_quotas)
    return QuotaSummary(**{name: p._asdict() for name, p in progress.items()})
