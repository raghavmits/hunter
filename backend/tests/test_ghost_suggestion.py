"""The ghost-suggestion rule (issue #11) — no database, plain Thread instances."""

import pytest
from app.cadence import is_ghost_suggested
from app.models import Thread, ThreadStatus

GHOST_THRESHOLD = 3


@pytest.mark.parametrize(
    ("nudge_number", "expected"),
    [(0, False), (2, False), (3, True), (4, True)],
)
def test_boundary_at_the_threshold(nudge_number, expected) -> None:
    thread = Thread(nudge_number=nudge_number, status=ThreadStatus.OPEN)
    assert is_ghost_suggested(thread, GHOST_THRESHOLD) is expected


@pytest.mark.parametrize(
    "status",
    [ThreadStatus.REJECTED, ThreadStatus.GHOSTED, ThreadStatus.WITHDRAWN, ThreadStatus.CLOSED],
)
def test_terminal_status_is_never_ghost_suggested(status) -> None:
    thread = Thread(nudge_number=5, status=status)
    assert is_ghost_suggested(thread, GHOST_THRESHOLD) is False


def test_open_thread_past_threshold_is_ghost_suggested() -> None:
    thread = Thread(nudge_number=10, status=ThreadStatus.OPEN)
    assert is_ghost_suggested(thread, GHOST_THRESHOLD) is True
