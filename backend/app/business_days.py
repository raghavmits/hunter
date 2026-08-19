"""Business-day date arithmetic (issue #9). Pure logic — no DB, no framework.

Holidays are out of scope for v1 (PLAN.md §6.8): only Saturday/Sunday are
skipped.
"""

import datetime

_WEEKEND = (5, 6)  # date.weekday(): Monday=0 ... Saturday=5, Sunday=6


def add_business_days(start: datetime.date, n: int) -> datetime.date:
    """The date n business days after start. start itself is never counted.

    n == 0 returns start unchanged, even on a weekend — this is the
    identity case, not "roll forward to the next weekday". Negative n
    walks backward.
    """
    current = start
    step = 1 if n >= 0 else -1
    remaining = abs(n)

    while remaining > 0:
        current += datetime.timedelta(days=step)
        if current.weekday() not in _WEEKEND:
            remaining -= 1

    return current


def count_business_days(start: datetime.date, end: datetime.date) -> int:
    """The inverse of add_business_days: count_business_days(s, add_business_days(s, n)) == n.

    Negative when end is before start.
    """
    if end == start:
        return 0

    step = 1 if end > start else -1
    sign = 1 if end > start else -1
    current = start
    count = 0

    while current != end:
        current += datetime.timedelta(days=step)
        if current.weekday() not in _WEEKEND:
            count += 1

    return sign * count
