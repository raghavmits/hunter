"""POST/GET /api/threads (issues #14, #15, #16)."""

from datetime import UTC, date, datetime

from fastapi import APIRouter, HTTPException

from app.cadence import compute_cadence, is_ghost_suggested
from app.config import get_config
from app.db import DbSession
from app.models import Motion, RoleFamily, Stage, Thread, ThreadStatus
from app.repositories import (
    CompanyRepository,
    ContactRepository,
    StageEventRepository,
    ThreadRepository,
    TouchRepository,
)
from app.schemas.company import CompanyRead
from app.schemas.contact import ContactRead
from app.schemas.stage_event import StageEventRead
from app.schemas.thread import ThreadCreate, ThreadDetail, ThreadRead, TouchLogged
from app.schemas.touch import TouchCreate, TouchRead

router = APIRouter(prefix="/threads", tags=["threads"])


def _days_in_stage(thread: Thread) -> int:
    """Calendar days, not business days — FR-12's at-risk rule sits outside
    FR-7's cadence table, the one place PLAN.md is explicit about business days.

    stage_entered_at comes back from SQLite as a naive datetime representing
    UTC (SQLAlchemy's server_default=func.now() compiles to CURRENT_TIMESTAMP,
    which SQLite always reports in UTC) — comparing it against naive local
    time silently produced negative day counts on any machine not on UTC.
    """
    now_utc = datetime.now(UTC).replace(tzinfo=None)
    return (now_utc - thread.stage_entered_at).days


def _to_thread_read(thread: Thread, ghost_threshold: int) -> ThreadRead:
    return ThreadRead(
        id=thread.id,
        company_id=thread.company_id,
        contact_id=thread.contact_id,
        role_title=thread.role_title,
        role_family=thread.role_family,
        motion=thread.motion,
        stage=thread.stage,
        status=thread.status,
        stage_entered_at=thread.stage_entered_at,
        next_follow_up_date=thread.next_follow_up_date,
        nudge_number=thread.nudge_number,
        follow_up_pinned=thread.follow_up_pinned,
        referral_promised=thread.referral_promised,
        referral_submitted_at=thread.referral_submitted_at,
        jd_url=thread.jd_url,
        notes=thread.notes,
        created_at=thread.created_at,
        closed_at=thread.closed_at,
        is_ghost_suggested=is_ghost_suggested(thread, ghost_threshold),
        days_in_stage=_days_in_stage(thread),
    )


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
    return _to_thread_read(thread, get_config().ghost_threshold)


@router.get("", response_model=list[ThreadRead])
def list_threads(
    db: DbSession,
    status: ThreadStatus | None = None,
    stage: Stage | None = None,
    motion: Motion | None = None,
    role_family: RoleFamily | None = None,
) -> list[ThreadRead]:
    threads = ThreadRepository(db).list(
        status=status, stage=stage, motion=motion, role_family=role_family
    )
    ghost_threshold = get_config().ghost_threshold
    return [_to_thread_read(t, ghost_threshold) for t in threads]


@router.get("/{thread_id}", response_model=ThreadDetail)
def get_thread(thread_id: int, db: DbSession) -> ThreadDetail:
    thread = ThreadRepository(db).get(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    base = _to_thread_read(thread, get_config().ghost_threshold)
    touches = TouchRepository(db).list_for_thread(thread_id)
    stage_events = StageEventRepository(db).list_for_thread(thread_id)

    return ThreadDetail(
        **base.model_dump(),
        company=CompanyRead.model_validate(thread.company),
        contact=ContactRead.model_validate(thread.contact) if thread.contact else None,
        touches=[TouchRead.model_validate(t) for t in touches],
        stage_events=[StageEventRead.model_validate(e) for e in stage_events],
    )


@router.post("/{thread_id}/touches", response_model=TouchLogged, status_code=201)
def log_touch(thread_id: int, body: TouchCreate, db: DbSession) -> TouchLogged:
    thread_repo = ThreadRepository(db)
    thread = thread_repo.get(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    occurred_at = body.occurred_at if body.occurred_at is not None else date.today()

    touch = TouchRepository(db).create(
        thread_id=thread_id,
        kind=body.kind,
        direction=body.direction,
        channel=body.channel,
        occurred_at=occurred_at,
        note=body.note,
    )

    result = compute_cadence(
        kind=body.kind,
        direction=body.direction,
        occurred_at=occurred_at,
        current_nudge_number=thread.nudge_number,
        follow_up_pinned=thread.follow_up_pinned,
        cadence=get_config().cadence,
    )
    update_fields: dict[str, object] = {"nudge_number": result.nudge_number}
    if result.should_update_date:
        update_fields["next_follow_up_date"] = result.next_follow_up_date
    updated_thread = thread_repo.update(thread_id, **update_fields)
    assert updated_thread is not None  # just fetched above, can't have vanished mid-request

    db.commit()
    return TouchLogged(
        touch=TouchRead.model_validate(touch),
        thread=_to_thread_read(updated_thread, get_config().ghost_threshold),
    )
