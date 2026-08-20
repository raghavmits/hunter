"""Pure corpus filesystem logic (issue #36) — resolve_path's traversal guard
tested directly, since HTTP-level testing fights the client's own URL
normalization (see test_corpus_endpoints.py's comment on that)."""

import pytest
from app.corpus import CorpusPathError, _frontmatter_fields, _split_frontmatter, resolve_path


def test_resolve_path_accepts_a_normal_path(tmp_path) -> None:
    (tmp_path / "resume").mkdir()
    target = tmp_path / "resume" / "resume.md"
    target.write_text("hi")

    assert resolve_path(tmp_path, "resume/resume.md") == target.resolve()


def test_resolve_path_rejects_traversal(tmp_path) -> None:
    with pytest.raises(CorpusPathError):
        resolve_path(tmp_path, "../secret.md")


def test_resolve_path_rejects_nested_traversal(tmp_path) -> None:
    with pytest.raises(CorpusPathError):
        resolve_path(tmp_path, "resume/../../secret.md")


def test_resolve_path_rejects_non_markdown(tmp_path) -> None:
    with pytest.raises(CorpusPathError):
        resolve_path(tmp_path, "resume/resume.pdf")


def test_malformed_yaml_falls_back_to_no_frontmatter() -> None:
    text = '---\ntitle: "unterminated\n  bad: [1,2\n---\n\nBody text.\n'

    frontmatter, body = _split_frontmatter(text)

    assert frontmatter == {}
    assert body == text  # the whole file, untouched — nothing to safely strip


def test_wrong_field_types_normalize_to_safe_defaults() -> None:
    data: dict[str, object] = {"title": 123, "tags": "not-a-list", "updated": [1, 2]}

    title, tags, updated = _frontmatter_fields(data)

    assert (title, tags, updated) == (None, [], None)
