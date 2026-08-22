from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/hunter"

engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
