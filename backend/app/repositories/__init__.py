"""Repositories (issue #8) — the app's only way to read or write the database.

Nothing outside this package should import SQLAlchemy to touch a table.
"""

from app.repositories.company import CompanyRepository
from app.repositories.contact import ContactRepository
from app.repositories.stage_event import StageEventRepository
from app.repositories.thread import ThreadRepository
from app.repositories.touch import TouchRepository

__all__ = [
    "CompanyRepository",
    "ContactRepository",
    "StageEventRepository",
    "ThreadRepository",
    "TouchRepository",
]
