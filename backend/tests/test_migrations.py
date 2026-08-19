"""alembic upgrade head / downgrade base against a real temp database (issue #4).

Checks the migration chain generically (every table gets dropped by downgrade
base, alembic_version always exists) rather than pinning an exact table set,
so this test doesn't need editing every time a new table lands (#5, #6, #7).
"""

import os
import sqlite3
import subprocess
from pathlib import Path

from app.db import DATABASE_URL_ENV_VAR

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_alembic(*args: str, db_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "alembic", *args],
        cwd=REPO_ROOT,
        env={**os.environ, DATABASE_URL_ENV_VAR: f"sqlite:///{db_path}"},
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_upgrade_head_then_downgrade_base_round_trips_cleanly(tmp_path) -> None:
    db_path = tmp_path / "migrations_test.db"

    upgraded = _run_alembic("upgrade", "head", db_path=db_path)
    assert upgraded.returncode == 0, upgraded.stderr

    conn = sqlite3.connect(db_path)
    tables_after_upgrade = {
        row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    version = conn.execute("SELECT version_num FROM alembic_version").fetchall()
    conn.close()
    assert "alembic_version" in tables_after_upgrade
    assert len(version) == 1

    downgraded = _run_alembic("downgrade", "base", db_path=db_path)
    assert downgraded.returncode == 0, downgraded.stderr

    conn = sqlite3.connect(db_path)
    tables_after_downgrade = {
        row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    version_after = conn.execute("SELECT version_num FROM alembic_version").fetchall()
    conn.close()
    assert tables_after_downgrade == {"alembic_version"}  # every app table dropped
    assert version_after == []
