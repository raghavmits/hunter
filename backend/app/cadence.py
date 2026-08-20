"""Cadence engine (issue #10): given a touch, compute the new follow-up state.

The cadence table is a parameter, not read internally via app.config.get_config()
— keeps this a pure, directly-testable function. Callers pass get_config().cadence.
"""

from datetime import date, datetime
from typing import NamedTuple

from app.business_days import add_business_days
from app.config import CadenceEntry
from app.models import Thread, ThreadStatus, TouchDirection, TouchKind


class CadenceResult(NamedTuple):
    next_follow_up_date: date | None
    should_update_date: bool
    nudge_number: int


def compute_cadence(
    kind: TouchKind,
    direction: TouchDirection,
    occurred_at: date,
    current_nudge_number: int,
    follow_up_pinned: bool,
    cadence: dict[str, CadenceEntry],
) -> CadenceResult:
    if direction == TouchDirection.INBOUND:
        new_nudge_number = 0
        next_follow_up_date = None
    else:
        new_nudge_number = current_nudge_number + 1
        next_follow_up_date = _next_follow_up_date(kind, new_nudge_number, occurred_at, cadence)

    if follow_up_pinned:
        return CadenceResult(
            next_follow_up_date=None, should_update_date=False, nudge_number=new_nudge_number
        )

    return CadenceResult(
        next_follow_up_date=next_follow_up_date,
        should_update_date=True,
        nudge_number=new_nudge_number,
    )


def is_ghost_suggested(thread: Thread, ghost_threshold: int) -> bool:
    """Issue #11. Never closes anything — a derived read, not a stored column.

    "No inbound touch since" needs no separate check: #10's cadence engine
    already resets nudge_number to 0 on every inbound touch, so
    nudge_number is already an accurate count of consecutive unanswered
    outbound touches. A thread already in a terminal status is never
    flagged — there's nothing left to suggest for one that's already closed.
    """
    return thread.status == ThreadStatus.OPEN and thread.nudge_number >= ghost_threshold


def days_in_stage(thread: Thread, now_utc: datetime) -> int:
    """Issue #15, moved here (issue #19) so #19's digest can share it without
    duplicating the UTC fix. Calendar days, not business days — FR-12's
    at-risk rule sits outside FR-7's cadence table, the one place PLAN.md is
    explicit about business days.

    `now_utc` is a required parameter, not computed internally via
    datetime.now() — otherwise this isn't actually a pure function of its
    inputs, it's silently reading the wall clock, which is exactly the kind
    of hidden dependency #10/#11 deliberately avoided (cadence and
    ghost_threshold are both parameters, not fetched internally). Callers
    pass datetime.now(UTC).replace(tzinfo=None) — naive UTC, comparable to
    stage_entered_at (see the note below on why it must be UTC).

    stage_entered_at comes back from SQLite as a naive datetime representing
    UTC (SQLAlchemy's server_default=func.now() compiles to CURRENT_TIMESTAMP,
    which SQLite always reports in UTC) — comparing it against naive local
    time silently produced negative day counts on any machine not on UTC.
    """
    return (now_utc - thread.stage_entered_at).days


def _next_follow_up_date(
    kind: TouchKind, nudge_number: int, occurred_at: date, cadence: dict[str, CadenceEntry]
) -> date | None:
    entry = cadence[kind.value]
    index = nudge_number - 1

    if index < len(entry.intervals):
        interval = entry.intervals[index]
    elif entry.recurring:
        interval = entry.intervals[-1]
    else:
        return None  # cadence exhausted — #11's ghost suggestion takes over from here

    return add_business_days(occurred_at, interval)
