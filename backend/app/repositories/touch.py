"""Repository for touch (issue #8). Append-only, per #7 — no update method."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Touch, TouchChannel, TouchDirection, TouchKind


class TouchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_thread(self, thread_id: int) -> list[Touch]:
        stmt = select(Touch).where(Touch.thread_id == thread_id).order_by(Touch.occurred_at.asc())
        return list(self.session.execute(stmt).scalars().all())

    def list_by_occurred_at(self, occurred_at: date) -> list[Touch]:
        """Issue #20: every touch on a given day, across all threads — the
        quota endpoint groups these by kind/direction itself."""
        stmt = select(Touch).where(Touch.occurred_at == occurred_at)
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self) -> list[Touch]:
        """Issue #21: every touch, all-time, across all threads — the targets
        endpoint's input counts are cumulative, unlike #20's daily ones."""
        return list(self.session.execute(select(Touch)).scalars().all())

    def create(
        self,
        thread_id: int,
        kind: TouchKind,
        direction: TouchDirection,
        channel: TouchChannel,
        occurred_at: date,
        note: str | None = None,
    ) -> Touch:
        touch = Touch(
            thread_id=thread_id,
            kind=kind,
            direction=direction,
            channel=channel,
            occurred_at=occurred_at,
            note=note,
        )
        self.session.add(touch)
        self.session.flush()
        return touch
