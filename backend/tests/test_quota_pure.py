"""build_quota_progress as a pure function over plain Touch objects (issue #20)."""

import datetime

from app.config import DailyQuotas
from app.models import Touch, TouchChannel, TouchDirection, TouchKind
from app.quota import build_quota_progress

QUOTAS = DailyQuotas(
    cold_outreach_sent=10,
    warm_intro_requests_sent=6,
    cold_applications_submitted=6,
    referral_asks_made=3,
)


def _touch(kind: TouchKind, direction: TouchDirection) -> Touch:
    return Touch(
        kind=kind,
        direction=direction,
        channel=TouchChannel.EMAIL,
        occurred_at=datetime.date(2026, 1, 1),
    )


def test_no_touches_all_zero() -> None:
    result = build_quota_progress([], QUOTAS)

    assert result["cold_outreach_sent"] == (0, 10, 10)


def test_inbound_touches_do_not_count() -> None:
    touches = [_touch(TouchKind.COLD_OUTREACH, TouchDirection.INBOUND)]

    result = build_quota_progress(touches, QUOTAS)

    assert result["cold_outreach_sent"].count == 0


def test_referral_promised_maps_to_referral_asks_made() -> None:
    touches = [_touch(TouchKind.REFERRAL_PROMISED, TouchDirection.OUTBOUND)]

    result = build_quota_progress(touches, QUOTAS)

    assert result["referral_asks_made"].count == 1


def test_kind_with_no_quota_mapping_is_ignored() -> None:
    touches = [_touch(TouchKind.POST_INTERVIEW, TouchDirection.OUTBOUND)]

    result = build_quota_progress(touches, QUOTAS)

    assert sum(p.count for p in result.values()) == 0
