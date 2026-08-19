"""Shared fixtures (issue #4)."""

import pytest
from app.db import DATABASE_URL_ENV_VAR, _build_engine, _build_sessionmaker


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point HUNTER_DATABASE_URL at an isolated temp-file SQLite database."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv(DATABASE_URL_ENV_VAR, f"sqlite:///{db_path}")
    yield db_path
    _build_engine.cache_clear()
    _build_sessionmaker.cache_clear()
