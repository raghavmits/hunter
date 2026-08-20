#!/usr/bin/env python3
"""Fill a scratch SQLite file with realistic demo data (issue #39).

    uv run python scripts/seed_demo_data.py [path]

Defaults to demo.db at the repo root (gitignored) — never touches the
real, tracked hunter.db. Schema is built the same way the test suite
builds it (Base.metadata.create_all), not via Alembic — this is throwaway
output, not something migrations need to track.
"""

import sys
from datetime import UTC, date, datetime
from pathlib import Path

from app.db import Base
from app.seed import seed_demo_data
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = REPO_ROOT / "demo.db"


def main() -> None:
    db_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_PATH
    if db_path.exists():
        db_path.unlink()

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    today = date.today()
    now_utc = datetime.now(UTC).replace(tzinfo=None)

    with Session(engine) as session:
        ids = seed_demo_data(session, today=today, now_utc=now_utc)
        session.commit()

    print(f"Seeded {db_path} with {len(ids)} threads:")
    for name, thread_id in ids.items():
        print(f"  {name}: {thread_id}")


if __name__ == "__main__":
    main()
