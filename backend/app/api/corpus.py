"""GET /api/corpus, /api/corpus/{path}, /api/corpus/search (issue #36)."""

from fastapi import APIRouter, HTTPException, Query

from app.corpus import (
    CorpusFileNotFoundError,
    CorpusPathError,
    corpus_root,
    list_entries,
    read_file,
)
from app.corpus import (
    search as search_corpus,
)
from app.schemas.corpus import CorpusEntry, CorpusEntryList
from app.schemas.corpus import CorpusFile as CorpusFileSchema

router = APIRouter(prefix="/corpus", tags=["corpus"])


@router.get("", response_model=CorpusEntryList)
def get_corpus_entries() -> CorpusEntryList:
    entries = list_entries(corpus_root())
    return CorpusEntryList(
        entries=[
            CorpusEntry(path=e.path, title=e.title, tags=e.tags, updated=e.updated) for e in entries
        ]
    )


@router.get("/search", response_model=CorpusEntryList)
def search_corpus_entries(q: str = Query(min_length=1)) -> CorpusEntryList:
    entries = search_corpus(corpus_root(), q)
    return CorpusEntryList(
        entries=[
            CorpusEntry(path=e.path, title=e.title, tags=e.tags, updated=e.updated) for e in entries
        ]
    )


@router.get("/{file_path:path}", response_model=CorpusFileSchema)
def get_corpus_file(file_path: str) -> CorpusFileSchema:
    try:
        file = read_file(corpus_root(), file_path)
    except CorpusPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except CorpusFileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="File not found") from exc

    return CorpusFileSchema(
        path=file.path, title=file.title, tags=file.tags, updated=file.updated, content=file.content
    )
