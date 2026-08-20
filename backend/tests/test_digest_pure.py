"""build_digest as a pure function over plain Thread objects (issue #19)."""

import datetime

from app.digest import build_digest
from app.models import Company, Stage, Thread

TODAY = datetime.date(2026, 1, 15)
NOW_UTC = datetime.datetime(2026, 1, 15, 12, 0, 0)


def _thread(**overrides) -> Thread:
    defaults = {
        "id": 1,
        "company": Company(id=1, name="Acme"),
        "company_id": 1,
        "contact": None,
        "contact_id": None,
        "stage": Stage.OUTREACH,
        "stage_entered_at": NOW_UTC,
        "next_follow_up_date": None,
        "nudge_number": 0,
    }
    defaults.update(overrides)
    return Thread(**defaults)


def test_empty_thread_list() -> None:
    result = build_digest([], at_risk_threshold_days=8, today=TODAY, now_utc=NOW_UTC)

    assert result.overdue == []
    assert result.due_today == []
    assert result.at_risk == []
    assert result.live_conversation_count == 0


def test_overdue_ranked_by_days_overdue_then_funnel_stage_order() -> None:
    a = _thread(id=1, next_follow_up_date=TODAY - datetime.timedelta(days=3), stage=Stage.OFFER)
    b = _thread(id=2, next_follow_up_date=TODAY - datetime.timedelta(days=3), stage=Stage.REPLIED)
    c = _thread(id=3, next_follow_up_date=TODAY - datetime.timedelta(days=5), stage=Stage.OUTREACH)

    result = build_digest([a, b, c], at_risk_threshold_days=8, today=TODAY, now_utc=NOW_UTC)

    # c is most overdue (5 days) regardless of stage; a and b tie at 3 days,
    # tie-broken by funnel order (replied before offer)
    assert [t.thread.id for t in result.overdue] == [3, 2, 1]


def test_at_risk_threshold_is_strictly_greater_than() -> None:
    exactly_at_threshold = _thread(id=1, stage_entered_at=NOW_UTC - datetime.timedelta(days=8))
    over_threshold = _thread(id=2, stage_entered_at=NOW_UTC - datetime.timedelta(days=9))

    result = build_digest(
        [exactly_at_threshold, over_threshold],
        at_risk_threshold_days=8,
        today=TODAY,
        now_utc=NOW_UTC,
    )

    assert [t.thread.id for t in result.at_risk] == [2]
