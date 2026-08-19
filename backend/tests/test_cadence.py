"""The cadence engine (issue #10) — table-driven against the real config.yaml."""

import datetime

import pytest
from app.business_days import add_business_days
from app.cadence import compute_cadence
from app.config import get_config
from app.models import TouchDirection, TouchKind

OCCURRED_AT = datetime.date(2026, 1, 5)  # a Monday, so interval math is unambiguous
CADENCE = get_config().cadence

# (kind, [expected interval per nudge level 1..N, extended one level past the
# table for kinds that stop, or matching the recurring interval for the one
# that doesn't])
EXPECTED_INTERVALS = {
    TouchKind.COLD_OUTREACH: [5, 10, 20, None],
    TouchKind.WARM_INTRO_REQUEST: [3, 6, 12, None],
    TouchKind.REFERRAL_PROMISED: [2, 5, 10, None],
    TouchKind.POST_RECRUITER_CALL: [3, 6, 12, None],
    TouchKind.POST_INTERVIEW: [3, 7, 12, None],
    TouchKind.APPLICATION_SUBMITTED: [7, 14, None],
    TouchKind.LONG_TERM_NURTURE: [90, 90, 90, 90],  # recurring
}


@pytest.mark.parametrize(
    ("kind", "intervals"),
    list(EXPECTED_INTERVALS.items()),
)
def test_outbound_touch_at_every_nudge_level(kind, intervals) -> None:
    nudge = 0
    for level, interval in enumerate(intervals, start=1):
        result = compute_cadence(
            kind=kind,
            direction=TouchDirection.OUTBOUND,
            occurred_at=OCCURRED_AT,
            current_nudge_number=nudge,
            follow_up_pinned=False,
            cadence=CADENCE,
        )
        assert result.nudge_number == level
        assert result.should_update_date is True
        expected_date = None if interval is None else add_business_days(OCCURRED_AT, interval)
        assert result.next_follow_up_date == expected_date, f"{kind} nudge level {level}"
        nudge = result.nudge_number


@pytest.mark.parametrize("starting_nudge", [0, 1, 3, 5])
def test_inbound_touch_clears_date_and_resets_nudge(starting_nudge) -> None:
    result = compute_cadence(
        kind=TouchKind.COLD_OUTREACH,
        direction=TouchDirection.INBOUND,
        occurred_at=OCCURRED_AT,
        current_nudge_number=starting_nudge,
        follow_up_pinned=False,
        cadence=CADENCE,
    )
    assert result.should_update_date is True
    assert result.next_follow_up_date is None
    assert result.nudge_number == 0


def test_pinned_thread_outbound_touch_does_not_update_date_but_nudge_advances() -> None:
    result = compute_cadence(
        kind=TouchKind.COLD_OUTREACH,
        direction=TouchDirection.OUTBOUND,
        occurred_at=OCCURRED_AT,
        current_nudge_number=1,
        follow_up_pinned=True,
        cadence=CADENCE,
    )
    assert result.should_update_date is False
    assert result.nudge_number == 2


def test_pinned_thread_inbound_touch_does_not_update_date_but_nudge_resets() -> None:
    result = compute_cadence(
        kind=TouchKind.COLD_OUTREACH,
        direction=TouchDirection.INBOUND,
        occurred_at=OCCURRED_AT,
        current_nudge_number=2,
        follow_up_pinned=True,
        cadence=CADENCE,
    )
    assert result.should_update_date is False
    assert result.nudge_number == 0
