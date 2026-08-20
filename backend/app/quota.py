"""Daily quota progress (issue #20): today's touches against config.yaml's
four daily quotas. Pure over an already-fetched list of touches — no DB
access here, mirrors #10/#11/#19's style.
"""

from typing import NamedTuple

from app.config import DailyQuotas
from app.models import Touch, TouchDirection, TouchKind

# Maps each quota name to the touch.kind it counts. referral_asks_made is the
# one non-obvious pairing: there's no touch.kind literally meaning "asked for
# a referral" — referral_promised is the closest and only reasonable match.
_QUOTA_TOUCH_KIND: dict[str, TouchKind] = {
    "cold_outreach_sent": TouchKind.COLD_OUTREACH,
    "warm_intro_requests_sent": TouchKind.WARM_INTRO_REQUEST,
    "cold_applications_submitted": TouchKind.APPLICATION_SUBMITTED,
    "referral_asks_made": TouchKind.REFERRAL_PROMISED,
}


class QuotaProgress(NamedTuple):
    count: int
    target: int
    remaining: int


def build_quota_progress(
    touches_today: list[Touch], daily_quotas: DailyQuotas
) -> dict[str, QuotaProgress]:
    """touches_today must already be filtered to occurred_at == today by the caller."""
    outbound_counts: dict[TouchKind, int] = {}
    for touch in touches_today:
        if touch.direction == TouchDirection.OUTBOUND:
            outbound_counts[touch.kind] = outbound_counts.get(touch.kind, 0) + 1

    result = {}
    for quota_name, kind in _QUOTA_TOUCH_KIND.items():
        count = outbound_counts.get(kind, 0)
        target = getattr(daily_quotas, quota_name)
        result[quota_name] = QuotaProgress(
            count=count, target=target, remaining=max(0, target - count)
        )

    return result
