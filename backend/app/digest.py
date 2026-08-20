"""The digest (issue #19): overdue, due-today, at-risk, and the live
conversation count — everything PLAN.md FR-12 (a), (b), (c), (e) needs.
(d), quota progress, is #20.

Pure over a list of already-fetched open threads — no DB access here,
mirrors #10/#11's style.
"""

from datetime import date, datetime
from typing import NamedTuple

from app.cadence import days_in_stage
from app.models import Stage, Thread

_STAGE_ORDER = {stage: index for index, stage in enumerate(Stage)}


class DigestRow(NamedTuple):
    thread: Thread
    days_overdue: int | None


class DigestResult(NamedTuple):
    overdue: list[DigestRow]
    due_today: list[DigestRow]
    at_risk: list[DigestRow]
    live_conversation_count: int


def build_digest(
    threads: list[Thread], at_risk_threshold_days: int, today: date, now_utc: datetime
) -> DigestResult:
    """threads must already be filtered to status == open by the caller.

    now_utc is a required parameter, same reasoning as days_in_stage: this
    stays a real pure function of its inputs rather than silently reading
    the wall clock.
    """
    overdue = []
    due_today = []
    at_risk = []
    live_conversation_count = 0

    for thread in threads:
        if thread.next_follow_up_date is not None:
            delta_days = (today - thread.next_follow_up_date).days
            if delta_days > 0:
                overdue.append(DigestRow(thread=thread, days_overdue=delta_days))
            elif delta_days == 0:
                due_today.append(DigestRow(thread=thread, days_overdue=0))

        if days_in_stage(thread, now_utc) > at_risk_threshold_days:
            at_risk.append(DigestRow(thread=thread, days_overdue=None))

        if thread.stage != Stage.OUTREACH:
            live_conversation_count += 1

    def _overdue_sort_key(row: DigestRow) -> tuple[int, int]:
        assert row.days_overdue is not None  # every row appended to `overdue` set this
        return (-row.days_overdue, _STAGE_ORDER[row.thread.stage])

    overdue.sort(key=_overdue_sort_key)

    return DigestResult(
        overdue=overdue,
        due_today=due_today,
        at_risk=at_risk,
        live_conversation_count=live_conversation_count,
    )
