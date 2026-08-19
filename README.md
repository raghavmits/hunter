# Hunter

A local, single-user job search tracker. Runs entirely on your machine — no
containers, no external services, no LLM.

See `docs/PLAN.md` for the design and `docs/tasks.md` for the backlog.

## Layout

```
backend/app/     FastAPI application package
backend/tests/   pytest suite
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
