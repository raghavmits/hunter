# AGENTS.md

Working notes for agents on this repo. Start here every session.

Project: a local, single-user job search tracker.

## Stack

FastAPI + SQLAlchemy + Alembic + Postgres on the backend, React + Vite + TypeScript
on the frontend. Python tooling is the Astral set: `uv`, `pytest`, `ruff`, `ty`.
No LLM dependency — the app must run offline and deterministically.

Backend lives in `app/`. Frontend lives in `frontend/` (no UI library, plain CSS).
API calls from the frontend proxy to `http://localhost:8000` via `frontend/vite.config.ts`.
Tests run against a `hunter_test` Postgres database (created automatically by the fixture).

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

- **Dependencies live in `pyproject.toml`, added with `uv add`.
- **Commit regularly.** Small, working commits with a message saying what changed
  and why. Do not let a session end with a large uncommitted diff.
- Leave the suite green. If a test fails and you did not cause it, say so rather
  than working around it.
- Do not edit `uv.lock` by hand; let `uv` write it, and commit it.
- Do not create alembic migrations by hand. Let alembic revision --autogenerate command handle them. 

## Documents

- `docs/process.md` - how work is organized

---

This is a starting point. Add to it as the project grows — new commands, new
conventions, anything a fresh session would otherwise have to rediscover.
