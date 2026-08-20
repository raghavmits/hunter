"""GET /api/funnel (issue #22)."""

from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter

from app.db import DbSession
from app.funnel import build_funnel
from app.models import Motion, RoleFamily
from app.repositories import StageEventRepository, ThreadRepository
from app.schemas.funnel import Funnel
from app.schemas.funnel import FunnelStage as FunnelStageSchema

router = APIRouter(prefix="/funnel", tags=["funnel"])

Window = Literal["today", "7d", "30d", "all"]


def _window_start(window: Window, now_utc: datetime) -> datetime | None:
    """None means unfiltered. Boundaries are UTC — stage_event.occurred_at is
    stored in UTC (#18), so "today" means the current UTC calendar day, not
    the user's local midnight. A known simplification for a single-user
    localhost app, not a bug — 7d/30d are simple rolling windows, not
    calendar-aligned, for the same reason."""
    if window == "today":
        return datetime(now_utc.year, now_utc.month, now_utc.day)
    if window == "7d":
        return now_utc - timedelta(days=7)
    if window == "30d":
        return now_utc - timedelta(days=30)
    return None


@router.get("", response_model=Funnel)
def get_funnel(
    db: DbSession,
    motion: Motion | None = None,
    role_family: RoleFamily | None = None,
    window: Window = "all",
) -> Funnel:
    matching_thread_ids = {
        t.id for t in ThreadRepository(db).list(motion=motion, role_family=role_family)
    }

    window_start = _window_start(window, datetime.now(UTC).replace(tzinfo=None))

    stage_events = [
        event
        for event in StageEventRepository(db).list_all()
        if event.thread_id in matching_thread_ids
        and (window_start is None or event.occurred_at >= window_start)
    ]

    return Funnel(
        stages=[
            FunnelStageSchema(
                stage=s.stage, count=s.count, conversion_from_previous=s.conversion_from_previous
            )
            for s in build_funnel(stage_events)
        ]
    )
