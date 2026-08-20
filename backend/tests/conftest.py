"""Shared fixtures (issue #4, #39)."""

from datetime import UTC, date, datetime

import pytest
from app.db import (
    DATABASE_URL_ENV_VAR,
    Base,
    _build_engine,
    _build_sessionmaker,
    get_database_url,
    get_engine,
)
from app.seed import seed_demo_data


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point HUNTER_DATABASE_URL at an isolated temp-file SQLite database."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv(DATABASE_URL_ENV_VAR, f"sqlite:///{db_path}")
    yield db_path
    _build_engine.cache_clear()
    _build_sessionmaker.cache_clear()


@pytest.fixture
def demo_data(temp_db):
    """A realistic dataset (#39) — shared by the digest/funnel/targets smoke
    tests instead of each seeding its own.

    Uses the real, current today/now_utc rather than a frozen date: the
    endpoints under test (GET /api/digest etc.) read the real wall clock
    internally, not a parameter this fixture could override, so seeding
    relative to a hardcoded date would silently disagree with what "today"
    means to the code being tested (an overdue-vs-due-today thread would
    land in the wrong bucket the moment the frozen date drifted from
    reality). seed_demo_data() itself is still exactly as deterministic as
    always — same inputs produce the same relative offsets — this fixture
    is just choosing "real now" as that input, matching what the app itself
    would choose.
    """
    Base.metadata.create_all(get_engine())
    today = date.today()
    now_utc = datetime.now(UTC).replace(tzinfo=None)

    session = _build_sessionmaker(get_database_url())()
    try:
        ids = seed_demo_data(session, today=today, now_utc=now_utc)
        session.commit()
    finally:
        session.close()

    return {"today": today, "now_utc": now_utc, "ids": ids}
