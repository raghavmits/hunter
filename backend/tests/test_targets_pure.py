"""build_targets as a pure function over plain Touch/StageEvent objects (issue #21)."""

import datetime

from app.config import CampaignTarget, TargetType
from app.models import StageEvent, StageOrTerminal, Touch, TouchChannel, TouchDirection, TouchKind
from app.targets import build_targets

CAMPAIGN_TARGETS = {
    "new_connections_made": CampaignTarget(target=60, type=TargetType.INPUT, deadline=None),
    "warm_outreach_with_acquaintances": CampaignTarget(
        target=60, type=TargetType.INPUT, deadline=None
    ),
    "cold_applications": CampaignTarget(target=100, type=TargetType.INPUT, deadline=None),
    "screens_recruiter_calls": CampaignTarget(target=60, type=TargetType.OUTCOME, deadline=None),
    "interviews": CampaignTarget(target=25, type=TargetType.OUTCOME, deadline=None),
    "offers": CampaignTarget(target=3, type=TargetType.OUTCOME, deadline=None),
}


def _touch(kind: TouchKind, direction: TouchDirection) -> Touch:
    return Touch(
        kind=kind,
        direction=direction,
        channel=TouchChannel.EMAIL,
        occurred_at=datetime.date(2026, 1, 1),
    )


def _event(thread_id: int, to_stage: StageOrTerminal) -> StageEvent:
    return StageEvent(
        thread_id=thread_id,
        from_stage=None,
        to_stage=to_stage,
        occurred_at=datetime.datetime(2026, 1, 1),
    )


def test_empty_input_and_output() -> None:
    result = build_targets([], [], CAMPAIGN_TARGETS)

    assert result["new_connections_made"] == (0, 60, "input", None)
    assert result["offers"] == (0, 3, "outcome", None)


def test_terminal_to_stage_events_do_not_crash_or_count_as_a_stage() -> None:
    events = [_event(1, StageOrTerminal.REJECTED)]

    result = build_targets([], events, CAMPAIGN_TARGETS)

    assert result["screens_recruiter_calls"].count == 0
    assert result["interviews"].count == 0
    assert result["offers"].count == 0


def test_same_thread_reaching_a_stage_twice_counts_once() -> None:
    events = [
        _event(1, StageOrTerminal.SCREEN),
        _event(1, StageOrTerminal.INTERVIEW),
        _event(1, StageOrTerminal.SCREEN),
    ]

    result = build_targets([], events, CAMPAIGN_TARGETS)

    assert result["screens_recruiter_calls"].count == 1


def test_inbound_touches_do_not_count_toward_inputs() -> None:
    touches = [_touch(TouchKind.COLD_OUTREACH, TouchDirection.INBOUND)]

    result = build_targets(touches, [], CAMPAIGN_TARGETS)

    assert result["new_connections_made"].count == 0
