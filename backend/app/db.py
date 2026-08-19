"""Engine, declarative base, and session dependency (issue #4).

No application tables live here — this is the harness #5-#8 build on.
"""

import os
from collections.abc import Generator
from functools import cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL_ENV_VAR = "HUNTER_DATABASE_URL"

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = _REPO_ROOT / "hunter.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DATABASE_PATH}"

BUSY_TIMEOUT_MS = 5000

# Alembic's recommended convention: every constraint gets a predictable name,
# which SQLite's batch-mode ALTER (recreate-and-swap) depends on being able
# to drop and recreate constraints by name.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    pass


Base.metadata.naming_convention = NAMING_CONVENTION


def get_database_url() -> str:
    return os.environ.get(DATABASE_URL_ENV_VAR) or DEFAULT_DATABASE_URL


def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    cursor.close()


@cache
def _build_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    if url.startswith("sqlite"):
        event.listen(engine, "connect", _set_sqlite_pragmas)
    return engine


def get_engine() -> Engine:
    """The engine for the current HUNTER_DATABASE_URL, built lazily and cached per URL."""
    return _build_engine(get_database_url())


@cache
def _build_sessionmaker(url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=_build_engine(url), autoflush=False, expire_on_commit=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency. Yields a session; never commits, closes on the way out."""
    session = _build_sessionmaker(get_database_url())()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Routers depend on this instead of writing `Session = Depends(get_db)` themselves —
# keeps the SQLAlchemy Session import confined to db.py and repositories/ (see #8's
# structural test) while still giving every endpoint a typed session parameter.
DbSession = Annotated[Session, Depends(get_db)]
