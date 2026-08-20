# Job Search Tracker — v1 Backlog

Derived from `docs/PLAN.md` (rev 5). The rev-4 backlog (40 tasks, full
backend + frontend + funnel + corpus) shipped in full and is archived on
`raghav/version1` — it is not being resumed. This backlog starts over at
Phase 0 per PLAN.md §3 and stays short on purpose: nothing past task 3 gets
written until Phase 0 has run for a week and earned it.

---

## Phase 0 — Mockup (no backend, no database)

## 1. Seed the mockup's data by hand
Goal: A JSON (or CSV) file holding today's real pipeline, ready for a page to render.
Description: Read `docs/reference/bottom-up.csv` and `docs/reference/top-down.csv` and hand-transcribe them into one flat file — one row per pursuit: `company`, `role_title`, `contact_name`, `motion` (warm/cold), `status` (`watching|contacted|talking|interviewing|closed`), `notes`. Use judgment on status/motion for rows the sheets don't state cleanly; the goal is a realistic starting set, not a perfect migration. No code in this task.

## 2. Static list page
Goal: One page renders the seed data as a table and lets me edit it.
Description: Build a single page (plain React or even static HTML+JS is fine) that reads the file from task 1 and renders Company / Role / Contact / Status / Notes as a table, sortable/filterable by status. Editing a row and adding a new one writes back to the same file (or localStorage, if that's faster to wire up) — no server round-trip needed. Per PLAN.md §3, do not add anything beyond this table.

## 3. Use it for a week, then re-check
Goal: A written answer to whether the list earned daily use.
Description: Open and update the page for real, at least once most days, for a week. At the end, record in PLAN.md §6 (or a new note) whether it was opened most days, and list anything reached for that wasn't on the screen. This determines whether Phase 1 starts as planned or the screen gets changed first.

---

## Phase 1 — Minimal backend (do not start before task 3's check passes)

Tasks below are a sketch, not committed — write the real ones against
whatever task 3 actually found before starting.

## 4. `pursuit` table and API
Goal: The mockup's one table, persisted for real.
Description: One FastAPI + SQLAlchemy + Alembic table matching PLAN.md §5 (`pursuit`: company, role_title, contact_name, motion, status, notes, updated_at), with create/list/update endpoints. No touch history, no follow-up dates — those aren't in the schema yet. Migrate task 1's seed data in as the first migration's data, not a separate importer.

## 5. List page against the real API
Goal: Same screen as Phase 0, backed by the database instead of a local file.
Description: Point the Phase 0 page at the new API instead of the local file/localStorage. No new columns, no new views — this task is a storage swap, per PLAN.md §3.

---

## Anything past this line

Follow-up dates/cadence, a digest, funnel/quotas/targets, the corpus,
CSV import tooling, multi-contact pursuits — all deferred per PLAN.md §4.
Each becomes its own task only when Phase 0 or real use of Phase 1
surfaces a concrete need for it, written up with that reason attached.
Do not bulk-reopen the rev-4 list.
