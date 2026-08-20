"""Campaign target progress (issue #21): all-time, status-agnostic counts
against config.yaml's six campaign targets. Pure over already-fetched
touches and stage_events — no DB access here, mirrors #10/#11/#19/#20's
style.
"""

from typing import NamedTuple

from app.config import CampaignTarget
from app.models import Stage, StageEvent, Touch, TouchDirection, TouchKind

# Input targets → touch.kind. new_connections_made has no obvious touch
# kind of its own — it's the one touch kind (cold_outreach) left over once
# the other two input targets and three outcome stages are accounted for,
# and semantically a cold outreach is the act of making a new connection.
_INPUT_TOUCH_KIND: dict[str, TouchKind] = {
    "new_connections_made": TouchKind.COLD_OUTREACH,
    "warm_outreach_with_acquaintances": TouchKind.WARM_INTRO_REQUEST,
    "cold_applications": TouchKind.APPLICATION_SUBMITTED,
}

# Outcome targets → the stage a thread must have reached at least once.
_OUTCOME_STAGE: dict[str, Stage] = {
    "screens_recruiter_calls": Stage.SCREEN,
    "interviews": Stage.INTERVIEW,
    "offers": Stage.OFFER,
}


class TargetProgress(NamedTuple):
    count: int
    target: int
    type: str
    deadline: str | None


def build_targets(
    touches: list[Touch],
    stage_events: list[StageEvent],
    campaign_targets: dict[str, CampaignTarget],
) -> dict[str, TargetProgress]:
    outbound_touch_counts: dict[TouchKind, int] = {}
    for touch in touches:
        if touch.direction == TouchDirection.OUTBOUND:
            outbound_touch_counts[touch.kind] = outbound_touch_counts.get(touch.kind, 0) + 1

    # Distinct threads reaching each stage, not raw event rows — a thread
    # that bounces through a stage twice (a #18 backward correction that
    # later moves forward again) must not count twice. StageOrTerminal
    # includes the four terminal values too (rejected/ghosted/withdrawn/
    # closed), which aren't valid Stage members — skip those, only stage
    # values are relevant to outcome counting.
    _stage_values = {s.value for s in Stage}
    threads_reaching_stage: dict[Stage, set[int]] = {}
    for event in stage_events:
        if event.to_stage.value not in _stage_values:
            continue
        to_stage = Stage(event.to_stage.value)
        threads_reaching_stage.setdefault(to_stage, set()).add(event.thread_id)

    result = {}
    for name, config in campaign_targets.items():
        if name in _INPUT_TOUCH_KIND:
            count = outbound_touch_counts.get(_INPUT_TOUCH_KIND[name], 0)
        elif name in _OUTCOME_STAGE:
            count = len(threads_reaching_stage.get(_OUTCOME_STAGE[name], set()))
        else:
            count = 0  # a config-defined target this module doesn't know how to count

        result[name] = TargetProgress(
            count=count, target=config.target, type=config.type.value, deadline=config.deadline
        )

    return result
