# AGENTS.md

Working notes for agents on this repo. Start here every session.

Project: a local, single-user job search tracker. The backlog of tasks is defined as Github issues. Read the task you are picking up plus the
PLAN.md sections it names — you should not need the other tasks.

## Stack

FastAPI + SQLAlchemy + Alembic + SQLite on the backend, React + Vite + TypeScript
on the frontend. Python tooling is the Astral set: `uv`, `pytest`, `ruff`, `ty`.
No LLM dependency anywhere in v1 — the app must run offline and deterministically.

## Commands

Run at the start of every session:

```bash
uv sync          # install/refresh the environment from uv.lock
uv run pytest    # full test suite — should be green before you change anything
```

Before handing work back:

```bash
uv run ruff format          # format
uv run ruff check --fix     # lint
uv run ty check             # type check
uv run pytest               # tests
```

Database and dev server:

```bash
uv run alembic upgrade head                    # apply migrations
uv run alembic revision --autogenerate -m "…"  # new migration after a model change
make dev                                       # backend + frontend together
```

## Rules

- **Dependencies live in `pyproject.toml`, added with `uv add`. Do not add one
  without asking first.** A new dependency is a decision, not an implementation
  detail — propose it with the reason and wait for an answer.
- **Commit regularly.** Small, working commits with a message saying what changed
  and why. Do not let a session end with a large uncommitted diff.
- Leave the suite green. If a test fails and you did not cause it, say so rather
  than working around it.
- Do not edit `uv.lock` by hand; let `uv` write it, and commit it.
- Config values — cadences, quotas, targets, thresholds — belong in `config.yaml`,
  not hardcoded.
- **`hunter.db` is tracked and committed** — it is the backup (PLAN.md §4). Commit it
  after a session that changed data, same as any other file. It's SQLite, so git can't
  merge two divergent copies: this is a single-user app on one machine, so that should
  not come up, but if a commit ever conflicts on `hunter.db`, don't try to hand-merge
  the binary — pick the copy with the data you want to keep (`git checkout --ours` or
  `--theirs`) and re-apply anything from the other side by hand. WAL sidecar files
  (`*.db-wal`, `*.db-shm`) are gitignored; they're transient, not source of truth.

## Documents

- `docs/process.md` - how work is organized
- Before writing tests, read `docs/testing-guidelines.md`
- For anything touching the UI, read `docs/design-system.md`

---

This is a starting point. Add to it as the project grows — new commands, new
conventions, anything a fresh session would otherwise have to rediscover.
