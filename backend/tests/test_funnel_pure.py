"""build_funnel as a pure function over plain StageEvent objects (issue #22)."""

import datetime

from app.funnel import build_funnel
from app.models import Stage, StageEvent, StageOrTerminal


def _event(thread_id: int, to_stage: StageOrTerminal) -> StageEvent:
    return StageEvent(
        thread_id=thread_id,
        from_stage=None,
        to_stage=to_stage,
        occurred_at=datetime.datetime(2026, 1, 1),
    )


def test_empty_input_all_zero_and_null_conversion() -> None:
    result = build_funnel([])

    by_stage = {r.stage: r for r in result}
    assert by_stage[Stage.OUTREACH].count == 0
    assert by_stage[Stage.OUTREACH].conversion_from_previous is None
    assert by_stage[Stage.REPLIED].conversion_from_previous is None


def test_distinct_threads_not_raw_rows() -> None:
    events = [
        _event(1, StageOrTerminal.SCREEN),
        _event(1, StageOrTerminal.SCREEN),  # duplicate for the same thread
    ]

    result = build_funnel(events)

    by_stage = {r.stage: r for r in result}
    assert by_stage[Stage.SCREEN].count == 1


def test_terminal_to_stage_events_are_ignored() -> None:
    events = [_event(1, StageOrTerminal.REJECTED)]

    result = build_funnel(events)  # must not raise

    assert all(r.count == 0 for r in result)


def test_conversion_rate_computed_correctly() -> None:
    events = [
        _event(1, StageOrTerminal.OUTREACH),
        _event(2, StageOrTerminal.OUTREACH),
        _event(1, StageOrTerminal.REPLIED),
    ]

    result = build_funnel(events)

    by_stage = {r.stage: r for r in result}
    assert by_stage[Stage.OUTREACH].count == 2
    assert by_stage[Stage.REPLIED].count == 1
    assert by_stage[Stage.REPLIED].conversion_from_previous == 0.5
