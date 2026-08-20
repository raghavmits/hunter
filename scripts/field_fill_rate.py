#!/usr/bin/env python3
"""Field fill-rate audit — the tooling for PLAN.md §8's two-week review,
not the review itself (issue #40). There's no two weeks of real usage
yet, so this only reports numbers against whatever's actually in the
database when you run it; it recommends removing nothing on its own.

    uv run python scripts/field_fill_rate.py [db_path]

Defaults to hunter.db at the repo root. Every nullable column across the
5 models is introspected from the model metadata, not hand-maintained —
this stays correct if a future migration adds or drops a nullable
column. Also reports which corpus/ subdirectories have real content
beyond the seeded README.md/template.md skeleton (#35).
"""

import sys
from pathlib import Path

from app.corpus import corpus_root, list_entries
from app.models import Company, Contact, StageEvent, Thread, Touch
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import Session

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "hunter.db"

MODELS = [Company, Contact, Thread, Touch, StageEvent]

SKELETON_FILENAMES = {"README.md", "template.md"}


def _nullable_columns(model):
    return [c for c in inspect(model).columns if c.nullable]


def column_fill_rates(session: Session) -> list[dict]:
    rows = []
    for model in MODELS:
        total = session.scalar(select(func.count()).select_from(model))
        for column in _nullable_columns(model):
            filled = session.scalar(select(func.count(column)).select_from(model)) if total else 0
            rows.append(
                {
                    "table": model.__tablename__,
                    "column": column.name,
                    "total_rows": total,
                    "filled": filled,
                    "fill_rate": (filled / total) if total else None,
                }
            )
    return rows


def corpus_content_status() -> list[dict]:
    entries = list_entries(corpus_root())
    directories: dict[str, list[str]] = {}
    for entry in entries:
        slash = entry.path.find("/")
        directory = entry.path[:slash] if slash != -1 else "(root)"
        directories.setdefault(directory, []).append(entry.path.rsplit("/", 1)[-1])

    status = []
    for directory, filenames in sorted(directories.items()):
        real_content = [f for f in filenames if f not in SKELETON_FILENAMES]
        status.append(
            {"directory": directory, "has_real_content": bool(real_content), "files": real_content}
        )
    return status


def main() -> None:
    db_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_DB_PATH
    if not db_path.is_file():
        print(f"No database at {db_path}", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        rows = column_fill_rates(session)

    print(f"Column fill rates ({db_path}):")
    for row in rows:
        if row["total_rows"] == 0:
            print(f"  {row['table']}.{row['column']}: no rows yet")
            continue
        pct = round(row["fill_rate"] * 100)
        print(
            f"  {row['table']}.{row['column']}: {row['filled']}/{row['total_rows']} filled ({pct}%)"
        )

    print()
    print("Corpus directories (beyond README.md/template.md):")
    for entry in corpus_content_status():
        if entry["has_real_content"]:
            print(f"  {entry['directory']}: {', '.join(entry['files'])}")
        else:
            print(f"  {entry['directory']}: nothing beyond the template skeleton")


if __name__ == "__main__":
    main()
