from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401 — registers models with Base.metadata
from app.database import Base, get_session
from app.main import app as hunter_app

TEST_DB_URL = "postgresql://postgres:postgres@localhost:5432/hunter_test"


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(db_engine) -> Generator[Session, None, None]:
    with db_engine.connect() as conn:
        transaction = conn.begin()
        with Session(bind=conn) as s:
            yield s
        transaction.rollback()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    def override_get_session() -> Generator[Session, None, None]:
        yield session

    hunter_app.dependency_overrides[get_session] = override_get_session
    yield TestClient(hunter_app)
    hunter_app.dependency_overrides.clear()
