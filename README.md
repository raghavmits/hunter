# Hunter

A local, single-user job search tracker. Runs entirely on your machine — no
containers, no external services, no LLM.

See `docs/PLAN.md` for the design and `docs/tasks.md` for the backlog.

## Layout

```
backend/app/     FastAPI application package
backend/tests/   pytest suite
frontend/        React + Vite + TypeScript app
docs/            plan, task backlog, working notes
```

## Getting started

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv sync          # create .venv and install everything from uv.lock
uv run pytest    # run the test suite
```

## Development commands

```bash
uv run ruff format          # format
uv run ruff check --fix     # lint
uv run ty check             # type check
uv run pytest               # tests
```

Run all four before handing work back; the suite should be green and lint and
type checks clean.

## Database

SQLite, one file (`hunter.db`) at the repo root — tracked and committed as the
backup (see AGENTS.md).

```bash
uv run alembic upgrade head   # apply migrations to hunter.db
```

Override which database is used (tests, a scratch copy, etc.) with:

```bash
HUNTER_DATABASE_URL="sqlite:////absolute/path/to/other.db" uv run alembic upgrade head
```

`HUNTER_DATABASE_URL` is a full SQLAlchemy URL and is read by both the app and
Alembic, so migrations always run against the same database the app would use.

## Frontend

Requires [Node.js](https://nodejs.org/) 20+.

```bash
cd frontend
npm install
npm run dev      # starts Vite on http://localhost:5173
```

The frontend expects the backend running too — its dev server proxies
`/api/*` requests to `http://localhost:8000`:

```bash
uv run uvicorn app.main:app --app-dir backend --reload
```

(A single command to start both together lands in #27.)

```bash
npm run build     # type-check (tsc -b) and production build
npm run lint       # oxlint
```
