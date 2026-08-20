"""Pydantic schemas for GET /api/corpus, /api/corpus/{path}, /api/corpus/search (issue #36)."""

from pydantic import BaseModel


class CorpusEntry(BaseModel):
    path: str
    title: str | None
    tags: list[str]
    updated: str | None


class CorpusEntryList(BaseModel):
    entries: list[CorpusEntry]


class CorpusFile(BaseModel):
    path: str
    title: str | None
    tags: list[str]
    updated: str | None
    content: str
