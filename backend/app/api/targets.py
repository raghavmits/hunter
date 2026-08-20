"""GET /api/targets (issue #21)."""

from fastapi import APIRouter

from app.config import get_config
from app.db import DbSession
from app.repositories import StageEventRepository, TouchRepository
from app.schemas.targets import TargetsSummary
from app.targets import build_targets

router = APIRouter(prefix="/targets", tags=["targets"])


@router.get("", response_model=TargetsSummary)
def get_targets(db: DbSession) -> TargetsSummary:
    touches = TouchRepository(db).list_all()
    stage_events = StageEventRepository(db).list_all()
    progress = build_targets(touches, stage_events, get_config().campaign_targets)
    return TargetsSummary(**{name: p._asdict() for name, p in progress.items()})
