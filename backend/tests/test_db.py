"""Engine, connection pragmas, and the session dependency (issue #4)."""

import os
import threading
from pathlib import Path

import pytest
from app.db import DATABASE_URL_ENV_VAR, DEFAULT_DATABASE_PATH, get_database_url, get_db, get_engine
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool


def test_default_url_points_at_hunter_db_in_the_repo_root(monkeypatch) -> None:
    monkeypatch.delenv(DATABASE_URL_ENV_VAR, raising=False)

    assert get_database_url() == f"sqlite:///{DEFAULT_DATABASE_PATH}"
    assert DEFAULT_DATABASE_PATH.name == "hunter.db"
    assert DEFAULT_DATABASE_PATH.parent.name == "hunter"  # the repo root, not backend/


def test_default_url_is_the_same_regardless_of_cwd(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv(DATABASE_URL_ENV_VAR, raising=False)
    from_here = get_database_url()

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        from_elsewhere = get_database_url()
    finally:
        os.chdir(old_cwd)

    assert from_here == from_elsewhere


def test_env_override_is_picked_up_without_reimporting_anything(temp_db) -> None:
    assert get_database_url() == f"sqlite:///{temp_db}"


def test_foreign_keys_enforced_on_two_independent_connections(temp_db) -> None:
    engine = get_engine()
    metadata = MetaData()
    Table("qa_parent", metadata, Column("id", Integer, primary_key=True))
    child = Table(
        "qa_child",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey("qa_parent.id")),
    )
    metadata.create_all(engine)

    for _ in range(2):  # two independently obtained connections from the same engine
        with engine.connect() as conn, pytest.raises(IntegrityError):
            conn.execute(child.insert().values(parent_id=999))
            conn.commit()


def test_wal_and_busy_timeout_on_a_fresh_connection(temp_db) -> None:
    engine = get_engine()

    with engine.connect() as conn:
        journal_mode = conn.execute(text("PRAGMA journal_mode")).scalar()
        busy_timeout = conn.execute(text("PRAGMA busy_timeout")).scalar()

    assert journal_mode == "wal"
    assert busy_timeout and busy_timeout > 0


def test_session_usable_from_a_thread_other_than_the_one_that_built_the_engine(temp_db) -> None:
    errors = []

    def worker() -> None:
        gen = get_db()
        try:
            session = next(gen)
            session.execute(text("SELECT 1"))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            next(gen, None)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    assert errors == []


@pytest.fixture
def scratch_client(temp_db):
    """A throwaway app exercising get_db(), separate from the real app/routers."""
    from sqlalchemy import String

    app = FastAPI()
    metadata = MetaData()
    scratch = Table(
        "qa_scratch",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("label", String),
    )
    metadata.create_all(get_engine())

    @app.get("/session-id")
    def session_id(db: Session = Depends(get_db)) -> dict[str, int]:
        return {"id": id(db)}

    @app.post("/write-without-commit")
    def write_without_commit(db: Session = Depends(get_db)) -> dict[str, bool]:
        db.execute(scratch.insert().values(label="never committed"))
        return {"ok": True}

    @app.post("/write-then-raise")
    def write_then_raise(db: Session = Depends(get_db)) -> dict[str, bool]:
        db.execute(scratch.insert().values(label="written before the raise"))
        raise ValueError("boom")

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, scratch


def test_two_requests_get_two_different_sessions(scratch_client) -> None:
    client, _ = scratch_client

    first = client.get("/session-id").json()["id"]
    second = client.get("/session-id").json()["id"]

    assert first != second


def test_dependency_does_not_commit_implicitly(scratch_client) -> None:
    client, scratch = scratch_client

    response = client.post("/write-without-commit")

    assert response.status_code == 200
    with get_engine().connect() as conn:
        assert conn.execute(scratch.select()).fetchall() == []


def test_exception_after_write_leaves_no_row_and_closes_the_session(scratch_client) -> None:
    client, scratch = scratch_client

    response = client.post("/write-then-raise")

    assert response.status_code == 500
    with get_engine().connect() as conn:
        assert conn.execute(scratch.select()).fetchall() == []
    # No connection leaked out of the pool once the request finished.
    pool = get_engine().pool
    assert isinstance(pool, QueuePool)
    assert pool.checkedout() == 0


def test_only_db_and_repositories_import_session_from_sqlalchemy() -> None:
    """db.py builds sessions; repositories/ (#8) are the only other place allowed
    to hold a Session type hint, since that's the whole point of a repository
    layer — everything else (routers, from #12 on) goes through a repository
    instead of importing SQLAlchemy to get one."""
    app_dir = Path(__file__).resolve().parents[1] / "app"
    allowed = {"db.py"} | {p.name for p in (app_dir / "repositories").glob("*.py")}
    offenders = []
    for path in app_dir.rglob("*.py"):
        if path.name in allowed:
            continue
        text_content = path.read_text()
        if "from sqlalchemy" in text_content and "Session" in text_content:
            offenders.append(str(path))

    assert offenders == []
