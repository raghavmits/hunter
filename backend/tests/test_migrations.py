"""alembic upgrade head / downgrade base against a real temp database (issue #4)."""

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
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    version = conn.execute("SELECT version_num FROM alembic_version").fetchall()
    conn.close()
    assert tables == {"alembic_version"}
    assert len(version) == 1

    downgraded = _run_alembic("downgrade", "base", db_path=db_path)
    assert downgraded.returncode == 0, downgraded.stderr

    conn = sqlite3.connect(db_path)
    version_after = conn.execute("SELECT version_num FROM alembic_version").fetchall()
    conn.close()
    assert version_after == []
