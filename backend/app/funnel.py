"""Funnel counts and conversion rates (issue #22). Pure over an already-
fetched, already-filtered (thread ids, time window) list of stage_events —
no DB access here, mirrors #19/#20/#21's style.
"""

from typing import NamedTuple

from app.models import Stage, StageEvent

_stage_values = {s.value for s in Stage}


class FunnelStage(NamedTuple):
    stage: Stage
    count: int
    conversion_from_previous: float | None


def build_funnel(stage_events: list[StageEvent]) -> list[FunnelStage]:
    """stage_events must already be filtered to the relevant thread ids and
    time window by the caller.

    Counting comes from stage_event history (distinct threads reaching each
    stage — same distinct-thread-not-raw-row logic #21 established for
    outcome targets), not each thread's current stage, so a thread that
    moved on (or closed) still counts. StageOrTerminal includes the four
    terminal to_stage values too — irrelevant to a stage funnel, skipped.
    """
    threads_reaching_stage: dict[Stage, set[int]] = {}
    for event in stage_events:
        if event.to_stage.value not in _stage_values:
            continue
        stage = Stage(event.to_stage.value)
        threads_reaching_stage.setdefault(stage, set()).add(event.thread_id)

    result = []
    previous_count: int | None = None
    for stage in Stage:
        count = len(threads_reaching_stage.get(stage, set()))
        conversion = None
        if previous_count is not None and previous_count > 0:
            conversion = count / previous_count
        result.append(FunnelStage(stage=stage, count=count, conversion_from_previous=conversion))
        previous_count = count

    return result
