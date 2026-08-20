"""Repository for thread (issue #8). No session.commit() — callers commit."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Motion, RoleFamily, Stage, Thread, ThreadStatus


class ThreadRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: int) -> Thread | None:
        return self.session.get(Thread, id)

    def list(
        self,
        status: ThreadStatus | None = None,
        stage: Stage | None = None,
        motion: Motion | None = None,
        role_family: RoleFamily | None = None,
        company_id: int | None = None,
    ) -> list[Thread]:
        stmt = select(Thread)
        if status is not None:
            stmt = stmt.where(Thread.status == status)
        if stage is not None:
            stmt = stmt.where(Thread.stage == stage)
        if motion is not None:
            stmt = stmt.where(Thread.motion == motion)
        if role_family is not None:
            stmt = stmt.where(Thread.role_family == role_family)
        if company_id is not None:
            stmt = stmt.where(Thread.company_id == company_id)
        return list(self.session.execute(stmt).scalars().all())

    def create(
        self,
        company_id: int,
        contact_id: int | None = None,
        role_title: str | None = None,
        role_family: RoleFamily | None = None,
        motion: Motion | None = None,
        jd_url: str | None = None,
    ) -> Thread:
        thread = Thread(
            company_id=company_id,
            contact_id=contact_id,
            role_title=role_title,
            role_family=role_family,
            motion=motion,
            jd_url=jd_url,
        )
        self.session.add(thread)
        self.session.flush()
        return thread

    def update(self, id: int, **fields: object) -> Thread | None:
        thread = self.get(id)
        if thread is None:
            return None
        for key, value in fields.items():
            setattr(thread, key, value)
        self.session.flush()
        return thread
