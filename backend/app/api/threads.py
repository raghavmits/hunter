"""POST/GET /api/threads (issues #14, #15, #16, #17, #18)."""

from datetime import UTC, date, datetime

from fastapi import APIRouter, HTTPException

from app.business_days import add_business_days
from app.cadence import compute_cadence, days_in_stage, is_ghost_suggested
from app.config import get_config
from app.db import DbSession
from app.models import Motion, RoleFamily, Stage, StageOrTerminal, Thread, ThreadStatus
from app.repositories import (
    CompanyRepository,
    ContactRepository,
    StageEventRepository,
    ThreadRepository,
    TouchRepository,
)
from app.schemas.company import CompanyRead
from app.schemas.contact import ContactRead
from app.schemas.stage_event import StageChange, StageEventRead
from app.schemas.thread import (
    FollowUpSet,
    Snooze,
    StageChanged,
    ThreadCreate,
    ThreadDetail,
    ThreadRead,
    TouchLogged,
)
from app.schemas.touch import TouchCreate, TouchRead

router = APIRouter(prefix="/threads", tags=["threads"])

_STAGE_VALUES = {s.value for s in Stage}


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
        days_in_stage=days_in_stage(thread, datetime.now(UTC).replace(tzinfo=None)),
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


@router.patch("/{thread_id}/follow-up", response_model=ThreadRead)
def set_follow_up(thread_id: int, body: FollowUpSet, db: DbSession) -> ThreadRead:
    thread_repo = ThreadRepository(db)
    thread = thread_repo.update(
        thread_id, next_follow_up_date=body.next_follow_up_date, follow_up_pinned=True
    )
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    db.commit()
    return _to_thread_read(thread, get_config().ghost_threshold)


@router.post("/{thread_id}/snooze", response_model=ThreadRead)
def snooze_thread(thread_id: int, body: Snooze, db: DbSession) -> ThreadRead:
    thread_repo = ThreadRepository(db)
    if thread_repo.get(thread_id) is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    # From today, not the thread's current date — a snooze pushing out an
    # already-overdue date wouldn't move it into the future. Also pins the
    # thread: without that, the next outbound touch's cadence recompute
    # (#16) would silently overwrite the snooze.
    new_date = add_business_days(date.today(), body.business_days)
    thread = thread_repo.update(thread_id, next_follow_up_date=new_date, follow_up_pinned=True)
    assert thread is not None  # existence just checked above

    db.commit()
    return _to_thread_read(thread, get_config().ghost_threshold)


@router.post("/{thread_id}/stage", response_model=StageChanged, status_code=201)
def change_stage(thread_id: int, body: StageChange, db: DbSession) -> StageChanged:
    thread_repo = ThreadRepository(db)
    thread = thread_repo.get(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    # from_stage reads the thread's actual current columns (status if
    # terminal, else stage), not the last recorded event — the two can
    # diverge, since #14 never writes an initial stage_event on creation.
    from_stage = StageOrTerminal(
        thread.status.value if thread.status != ThreadStatus.OPEN else thread.stage.value
    )

    stage_event = StageEventRepository(db).create(
        thread_id=thread_id,
        from_stage=from_stage,
        to_stage=body.to,
        occurred_at=datetime.now(UTC).replace(tzinfo=None),
        note=body.note,
    )

    if body.to.value in _STAGE_VALUES:
        # Moving to a stage un-terminates the thread — being "at a stage" means
        # actively pursued. stage_entered_at refreshes; closed_at is cleared,
        # since an open thread with a stale non-null closed_at from a previous
        # terminal transition would be inconsistent data (QA caught this).
        updated_thread = thread_repo.update(
            thread_id,
            stage=Stage(body.to.value),
            status=ThreadStatus.OPEN,
            stage_entered_at=datetime.now(UTC).replace(tzinfo=None),
            closed_at=None,
        )
    else:
        # Terminal: stage is left exactly as it was — "rejected at screen" vs.
        # "rejected at interview" is meaningful history, not something closing erases.
        updated_thread = thread_repo.update(
            thread_id,
            status=ThreadStatus(body.to.value),
            closed_at=datetime.now(UTC).replace(tzinfo=None),
        )
    assert updated_thread is not None  # just fetched above, can't have vanished mid-request

    db.commit()
    return StageChanged(
        stage_event=StageEventRead.model_validate(stage_event),
        thread=_to_thread_read(updated_thread, get_config().ghost_threshold),
    )
