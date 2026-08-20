"""Repository for stage_event (issue #8). Append-only, per #7 — no update method."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StageEvent, StageOrTerminal


class StageEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_thread(self, thread_id: int) -> list[StageEvent]:
        stmt = (
            select(StageEvent)
            .where(StageEvent.thread_id == thread_id)
            .order_by(StageEvent.occurred_at.asc())
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self) -> list[StageEvent]:
        """Issue #21: every stage_event, all-time, across all threads — the
        targets endpoint counts distinct threads reaching each stage."""
        return list(self.session.execute(select(StageEvent)).scalars().all())

    def create(
        self,
        thread_id: int,
        from_stage: StageOrTerminal | None,
        to_stage: StageOrTerminal,
        occurred_at: datetime,
        note: str | None = None,
    ) -> StageEvent:
        stage_event = StageEvent(
            thread_id=thread_id,
            from_stage=from_stage,
            to_stage=to_stage,
            occurred_at=occurred_at,
            note=note,
        )
        self.session.add(stage_event)
        self.session.flush()
        return stage_event
