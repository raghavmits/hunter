"""Business-day date arithmetic (issue #9)."""

import datetime

import pytest
from app.business_days import add_business_days, count_business_days

MONDAY = datetime.date(2026, 1, 5)
TUESDAY = datetime.date(2026, 1, 6)
FRIDAY = datetime.date(2026, 1, 2)
SATURDAY = datetime.date(2026, 1, 3)
SUNDAY = datetime.date(2026, 1, 4)


# --- add_business_days ------------------------------------------------


@pytest.mark.parametrize(
    ("start", "n", "expected"),
    [
        (MONDAY, 0, MONDAY),
        (SATURDAY, 0, SATURDAY),
        (SUNDAY, 0, SUNDAY),
        (MONDAY, 1, TUESDAY),
        (FRIDAY, 1, MONDAY),  # crosses a weekend
        (SATURDAY, 1, MONDAY),  # Sunday not counted, Monday is the 1st business day
        (SUNDAY, 1, MONDAY),
        (MONDAY, -1, FRIDAY),  # crosses a weekend backward
        (SATURDAY, -1, FRIDAY),
        (SUNDAY, -1, FRIDAY),
    ],
)
def test_add_business_days_exact_dates(start, n, expected) -> None:
    assert add_business_days(start, n) == expected


def test_add_business_days_multi_week_span() -> None:
    # 10 business days from a Monday is two full weeks later, same weekday.
    assert add_business_days(MONDAY, 10) == MONDAY + datetime.timedelta(weeks=2)


def test_add_business_days_negative_multi_week_span() -> None:
    assert add_business_days(MONDAY, -10) == MONDAY - datetime.timedelta(weeks=2)


@pytest.mark.parametrize("start", [MONDAY, TUESDAY, FRIDAY, SATURDAY, SUNDAY])
@pytest.mark.parametrize("n", [1, 2, 5, 20])
def test_add_business_days_result_is_always_a_weekday(start, n) -> None:
    assert add_business_days(start, n).weekday() < 5
    assert add_business_days(start, -n).weekday() < 5


# --- count_business_days -----------------------------------------------


def test_count_business_days_same_date_is_zero() -> None:
    assert count_business_days(MONDAY, MONDAY) == 0
    assert count_business_days(SATURDAY, SATURDAY) == 0


def test_count_business_days_negative_when_end_before_start() -> None:
    assert count_business_days(MONDAY, FRIDAY) == -1


# --- inverse relationship: the property both functions must satisfy ------


@pytest.mark.parametrize("start", [MONDAY, TUESDAY, FRIDAY, SATURDAY, SUNDAY])
@pytest.mark.parametrize("n", list(range(-30, 31)))
def test_count_is_the_inverse_of_add(start, n) -> None:
    end = add_business_days(start, n)
    assert count_business_days(start, end) == n
