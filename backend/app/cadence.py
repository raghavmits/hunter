"""Cadence engine (issue #10): given a touch, compute the new follow-up state.

The cadence table is a parameter, not read internally via app.config.get_config()
— keeps this a pure, directly-testable function. Callers pass get_config().cadence.
"""

from datetime import date
from typing import NamedTuple

from app.business_days import add_business_days
from app.config import CadenceEntry
from app.models import TouchDirection, TouchKind


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
