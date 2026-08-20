"""GET /api/corpus, /api/corpus/{path}, /api/corpus/search (issue #36)."""

import pytest
from app.corpus import CORPUS_PATH_ENV_VAR
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def corpus_dir(tmp_path, monkeypatch):
    monkeypatch.setenv(CORPUS_PATH_ENV_VAR, str(tmp_path))
    return tmp_path


@pytest.fixture
def client(corpus_dir):
    with TestClient(app) as client:
        yield client


def _write(root, relative_path: str, text: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_list_includes_frontmatter_and_frontmatter_less_files(client, corpus_dir) -> None:
    _write(corpus_dir, "README.md", "# Corpus\n\nNo frontmatter here.\n")
    _write(
        corpus_dir,
        "strategy/agencies.md",
        '---\ntitle: "Agencies"\ntags: ["strategy"]\nupdated: "2026-08-19"\n---\n\n- Scalr\n',
    )

    response = client.get("/api/corpus")

    assert response.status_code == 200
    entries = {e["path"]: e for e in response.json()["entries"]}
    assert entries["README.md"] == {"path": "README.md", "title": None, "tags": [], "updated": None}
    assert entries["strategy/agencies.md"] == {
        "path": "strategy/agencies.md",
        "title": "Agencies",
        "tags": ["strategy"],
        "updated": "2026-08-19",
    }


def test_list_sorted_by_path(client, corpus_dir) -> None:
    _write(corpus_dir, "b.md", "b")
    _write(corpus_dir, "a.md", "a")

    paths = [e["path"] for e in client.get("/api/corpus").json()["entries"]]

    assert paths == ["a.md", "b.md"]


def test_read_file_returns_parsed_frontmatter_and_stripped_content(client, corpus_dir) -> None:
    _write(
        corpus_dir,
        "stories/example.md",
        '---\ntitle: "Example"\ntags: ["leadership"]\nupdated: "2026-08-19"\n'
        "---\n\n# Situation\n\nText.\n",
    )

    response = client.get("/api/corpus/stories/example.md")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Example"
    assert body["tags"] == ["leadership"]
    assert body["updated"] == "2026-08-19"
    assert body["content"] == "# Situation\n\nText.\n"
    assert "---" not in body["content"]


def test_read_nonexistent_file_404s(client, corpus_dir) -> None:
    _write(corpus_dir, "README.md", "placeholder so the dir exists\n")

    response = client.get("/api/corpus/does/not/exist.md")

    assert response.status_code == 404


def test_read_traversal_attempt_400s(client, corpus_dir) -> None:
    outside = corpus_dir.parent / "secret.md"
    outside.write_text("should never be reachable")

    # %2e%2e survives httpx's own path normalization, unlike a literal "..",
    # so this actually exercises resolve_path()'s guard rather than just
    # hitting a route the client already collapsed away.
    response = client.get("/api/corpus/%2e%2e/secret.md")

    assert response.status_code == 400


def test_read_non_markdown_path_400s(client, corpus_dir) -> None:
    _write(corpus_dir, "resume/resume.pdf", "not really a pdf")

    response = client.get("/api/corpus/resume/resume.pdf")

    assert response.status_code == 400


def test_search_matches_content(client, corpus_dir) -> None:
    _write(
        corpus_dir,
        "stories/one.md",
        '---\ntitle: "One"\ntags: []\nupdated: null\n---\n\nMentions Acme.\n',
    )
    _write(
        corpus_dir,
        "stories/two.md",
        '---\ntitle: "Two"\ntags: []\nupdated: null\n---\n\nUnrelated.\n',
    )

    response = client.get("/api/corpus/search", params={"q": "acme"})

    assert response.status_code == 200
    assert [e["path"] for e in response.json()["entries"]] == ["stories/one.md"]


def test_search_matches_tags_even_when_content_does_not(client, corpus_dir) -> None:
    _write(
        corpus_dir,
        "strategy/note.md",
        '---\ntitle: "Note"\ntags: ["healthy-signal"]\nupdated: null\n---\n\n'
        "Some unrelated text.\n",
    )

    response = client.get("/api/corpus/search", params={"q": "healthy-signal"})

    assert [e["path"] for e in response.json()["entries"]] == ["strategy/note.md"]


def test_search_is_case_insensitive_and_reports_misses(client, corpus_dir) -> None:
    _write(
        corpus_dir,
        "stories/one.md",
        '---\ntitle: "One"\ntags: []\nupdated: null\n---\n\nMentions ACME.\n',
    )

    hit = client.get("/api/corpus/search", params={"q": "acme"})
    miss = client.get("/api/corpus/search", params={"q": "nonexistent-term"})

    assert [e["path"] for e in hit.json()["entries"]] == ["stories/one.md"]
    assert miss.json()["entries"] == []


def test_search_requires_nonempty_query(client, corpus_dir) -> None:
    response = client.get("/api/corpus/search", params={"q": ""})

    assert response.status_code == 422


def test_no_caching_between_requests(client, corpus_dir) -> None:
    _write(
        corpus_dir,
        "facts/note.md",
        '---\ntitle: "Note"\ntags: []\nupdated: null\n---\n\nOriginal.\n',
    )

    first = client.get("/api/corpus/facts/note.md").json()
    _write(
        corpus_dir, "facts/note.md", '---\ntitle: "Note"\ntags: []\nupdated: null\n---\n\nEdited.\n'
    )
    second = client.get("/api/corpus/facts/note.md").json()

    assert first["content"] == "Original.\n"
    assert second["content"] == "Edited.\n"
