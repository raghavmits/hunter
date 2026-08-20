"""Filesystem access to corpus/ (issue #36). No caching, anywhere — FR-17
says reads happen on request with no index table, and #35's files are
edited directly, so every call re-reads the filesystem fresh."""

import os
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

CORPUS_PATH_ENV_VAR = "HUNTER_CORPUS_PATH"
DEFAULT_CORPUS_PATH = Path(__file__).resolve().parents[2] / "corpus"

_yaml = YAML(typ="safe")


class CorpusPathError(Exception):
    """A requested path escapes the corpus root or isn't a markdown file."""


class CorpusFileNotFoundError(Exception):
    """A well-formed path doesn't correspond to an existing file."""


def corpus_root() -> Path:
    override = os.environ.get(CORPUS_PATH_ENV_VAR)
    return Path(override) if override else DEFAULT_CORPUS_PATH


def _split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    try:
        parsed = _yaml.load(text[3:end])
    except YAMLError:
        return {}, text
    body = text[end + 4 :].lstrip("\n")
    return (parsed if isinstance(parsed, dict) else {}), body


def _frontmatter_fields(data: dict[str, object]) -> tuple[str | None, list[str], str | None]:
    title = data.get("title")
    tags = data.get("tags")
    updated = data.get("updated")
    return (
        title if isinstance(title, str) else None,
        tags if isinstance(tags, list) else [],
        updated if isinstance(updated, str) else None,
    )


def resolve_path(root: Path, relative_path: str) -> Path:
    """Raises CorpusPathError for anything that escapes root or isn't markdown."""
    if not relative_path.endswith(".md"):
        raise CorpusPathError(f"{relative_path} is not a markdown file")

    candidate = (root / relative_path).resolve()
    resolved_root = root.resolve()
    if not candidate.is_relative_to(resolved_root):
        raise CorpusPathError(f"{relative_path} escapes the corpus root")

    return candidate


class CorpusEntry:
    def __init__(self, path: str, title: str | None, tags: list[str], updated: str | None) -> None:
        self.path = path
        self.title = title
        self.tags = tags
        self.updated = updated


def _entry_for(root: Path, file: Path) -> CorpusEntry:
    try:
        text = file.read_text()
    except OSError:
        text = ""
    frontmatter, _ = _split_frontmatter(text)
    title, tags, updated = _frontmatter_fields(frontmatter)
    return CorpusEntry(
        path=file.relative_to(root).as_posix(), title=title, tags=tags, updated=updated
    )


def list_entries(root: Path) -> list[CorpusEntry]:
    if not root.is_dir():
        return []
    files = sorted(root.rglob("*.md"), key=lambda f: f.relative_to(root).as_posix())
    return [_entry_for(root, f) for f in files]


class CorpusFile:
    def __init__(
        self, path: str, title: str | None, tags: list[str], updated: str | None, content: str
    ) -> None:
        self.path = path
        self.title = title
        self.tags = tags
        self.updated = updated
        self.content = content


def read_file(root: Path, relative_path: str) -> CorpusFile:
    """Raises CorpusPathError (traversal/non-.md) or CorpusFileNotFoundError."""
    resolved = resolve_path(root, relative_path)
    if not resolved.is_file():
        raise CorpusFileNotFoundError(relative_path)

    text = resolved.read_text()
    frontmatter, content = _split_frontmatter(text)
    title, tags, updated = _frontmatter_fields(frontmatter)
    return CorpusFile(path=relative_path, title=title, tags=tags, updated=updated, content=content)


def search(root: Path, query: str) -> list[CorpusEntry]:
    needle = query.lower()
    results = []
    for file in (
        sorted(root.rglob("*.md"), key=lambda f: f.relative_to(root).as_posix())
        if root.is_dir()
        else []
    ):
        try:
            text = file.read_text()
        except OSError:
            continue
        frontmatter, _ = _split_frontmatter(text)
        title, tags, updated = _frontmatter_fields(frontmatter)
        tag_match = any(needle in tag.lower() for tag in tags)
        if needle in text.lower() or tag_match:
            results.append(
                CorpusEntry(
                    path=file.relative_to(root).as_posix(), title=title, tags=tags, updated=updated
                )
            )
    return results
