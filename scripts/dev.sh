#!/usr/bin/env bash
# One command, both dev servers (issue #27). Assumes `uv sync` and
# `npm install` (in frontend/) have already been run — same prerequisite
# as every other command in the README.
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PIDS=()

# Recursively kills a process and everything descended from it. A plain
# `kill $pid` isn't enough here: `npm run dev` spawns a separate `vite`
# process, and uvicorn's --reload spawns its own worker subprocess one
# level below that — a single level of `pkill -P` misses the worker.
kill_tree() {
  local pid="$1"
  local child
  for child in $(pgrep -P "$pid" 2>/dev/null); do
    kill_tree "$child"
  done
  kill "$pid" 2>/dev/null || true
}

cleanup() {
  trap - INT TERM EXIT
  echo
  echo "Shutting down..."
  for pid in "${PIDS[@]}"; do
    kill_tree "$pid"
  done
}
trap cleanup INT TERM EXIT

uv run alembic upgrade head || exit 1

uv run uvicorn app.main:app --app-dir backend --reload --port 8000 &
PIDS+=("$!")

(cd frontend && npm run dev -- --port 5173) &
PIDS+=("$!")

wait
