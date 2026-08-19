# Job Search Tracker — v1 Backlog

Derived from `docs/PLAN.md` (rev 4). Each task is scoped to one working session and
written to be handed to someone who has read only this task and `docs/PLAN.md` —
not the other tasks. Tasks are ordered so that dependencies come first, but each one
states the surface it touches so it can be picked up in isolation.

Stack, as decided in the plan: FastAPI + SQLAlchemy + Alembic + SQLite on the backend,
React + Vite + TypeScript on the frontend, markdown corpus and `config.yaml` in the repo.
No LLM anywhere in v1.

---

## Foundation

## 1. Bootstrap the repo with a passing test
Goal: An empty but runnable Python project whose test suite passes on a clean checkout.
Description: Create the backend package layout (`backend/app/`, `backend/tests/`), a `pyproject.toml` with FastAPI, SQLAlchemy, Alembic, pytest, and httpx pinned, and a `.gitignore` covering `__pycache__`, `.venv`, and the SQLite file. Add a single trivial test that asserts the package imports, and a `README.md` section documenting how to create the virtualenv, install, and run `pytest`. Done when a fresh clone can go from zero to a green test run using only the documented commands.

## 2. FastAPI app skeleton with a health endpoint
Goal: A FastAPI application that starts locally and answers `GET /api/health`.
Description: Add an app factory that builds the FastAPI instance, mounts an `/api` router, and enables CORS for the Vite dev origin. Expose `GET /api/health` returning app name and version, and add a test using FastAPI's test client asserting a 200 and the expected JSON shape. No database access in this task.

## 3. Config file and typed loader
Goal: All tunable numbers live in one `config.yaml`, loaded once into a validated object.
Description: Write `config.yaml` at the repo root holding the cadence intervals per touch kind, the four daily quotas, the six campaign targets with their deadlines, the role families, the contact sources, the ghost threshold (3 nudges), and the at-risk threshold (8 days) — all values are specified in PLAN.md §6.3 and §6.5. Implement a loader that parses it into a typed structure (Pydantic models), fails loudly with a clear message on a missing or malformed key, and caches the result. Include tests for a valid load and for two malformed cases.

## 4. Database engine, session, and Alembic setup
Goal: A SQLite database file, a session dependency, and a working migration harness.
Description: Configure the SQLAlchemy engine against a repo-local SQLite file (path overridable by env var so tests use a temp file), add a declarative base and a request-scoped session dependency for FastAPI, and initialize Alembic with an env that reads the same URL. Enable SQLite foreign key enforcement via a connection pragma. Add a test that opens a session, runs `SELECT 1`, and confirms `alembic upgrade head` succeeds on an empty database.

---

## Data model

## 5. `company` and `contact` tables
Goal: The two reference tables exist with a migration and model tests.
Description: Implement the `company` and `contact` SQLAlchemy models exactly as specified in PLAN.md §7.1, including the `status` enum on company and the `warmth` and `source` enums on contact. `contact.company_id` must be nullable — the bottom-up sheet is full of people with no company. Generate the Alembic migration and add tests covering insert, the nullable FK, and enum rejection of an invalid value.

## 6. `thread` table
Goal: The central pursuit table exists with a migration and model tests.
Description: Implement the `thread` model per PLAN.md §7.1: FKs to company and contact (contact nullable), the `role_family` / `motion` / `stage` / `status` enums, `stage_entered_at`, `next_follow_up_date`, `nudge_number`, `follow_up_pinned`, the two referral fields, `jd_url`, `notes`, and timestamps. Add an index on `(status, next_follow_up_date)` since the digest query is the app's hottest path. Tests should cover creating a thread with only a company set, and the defaults for stage, status, and nudge number.

## 7. `touch` and `stage_event` tables
Goal: The two history tables exist with a migration and model tests.
Description: Implement `touch` (thread FK, `kind` keyed to the cadence table, `direction`, `channel`, `occurred_at`, `note`) and `stage_event` (thread FK, nullable `from_stage`, `to_stage`, `occurred_at`, `note`) per PLAN.md §7.1. Both are append-only history; do not add update paths. Tests should cover inserting a touch and a first stage event with a null `from_stage`, and cascading behaviour when a thread is deleted.

## 8. Repository layer over the models
Goal: A thin data-access layer so the rest of the app never imports SQLAlchemy directly.
Description: Add repository classes for company, contact, thread, touch, and stage_event exposing the operations the app actually needs — get by id, list with simple filters, create, update, and the history appends. Keep the interfaces free of SQLAlchemy types so the database stays swappable, as PLAN.md FR-1 requires. Cover each repository with tests against an in-memory or temp-file SQLite database.

---

## Follow-up engine

## 9. Business-day date arithmetic
Goal: A small, well-tested utility for adding business days to a date.
Description: Implement `add_business_days(start, n)` that skips Saturdays and Sundays, plus a helper for counting business days between two dates. Holidays are out of scope for v1. This is pure logic with no database or framework dependency; test it thoroughly including weekend starts, zero and negative offsets, and multi-week spans.

## 10. Cadence engine
Goal: Given a touch and a thread, compute the next follow-up date and nudge number.
Description: Implement a pure function that takes the touch kind, direction, occurrence date, current nudge number, and the `follow_up_pinned` flag, and returns the new `next_follow_up_date` and `nudge_number` using the cadence table in PLAN.md FR-7 and the business-day helper. An outbound touch advances the nudge and sets the date from the table; an inbound touch clears the date and resets the nudge to zero; a pinned thread keeps its manual date regardless. Table-driven tests should cover every touch kind at every nudge level plus the pinned and inbound cases.

## 11. Ghost suggestion rule
Goal: The app can say "this thread looks ghosted" without ever closing anything itself.
Description: Implement a rule that flags a thread as ghost-suggested once `nudge_number` reaches the configured threshold (3) with no inbound touch since, and expose it as a derived boolean on thread reads rather than a stored column. Per PLAN.md FR-11 the app only suggests — closing stays a user action. Test the boundary at 2, 3, and 4 nudges and the reset after an inbound touch.

---

## API surface

## 12. Companies API
Goal: Create, read, update, and list companies over HTTP.
Description: Add `/api/companies` endpoints backed by the company repository, with Pydantic request and response schemas covering name, url, why_interested, and status. List should support a text filter on name and a filter by status. Test the happy paths plus validation failure on a missing name.

## 13. Contacts API
Goal: Create, read, update, and list contacts over HTTP.
Description: Add `/api/contacts` endpoints with schemas covering the full contact model, including the `warmth` and `source` enums whose allowed values come from `config.yaml`. A contact must be creatable with no company. Test creation with and without a company, the source enum validation, and listing filtered by company.

## 14. Quick-add thread endpoint
Goal: One endpoint that creates a thread with only a company name required.
Description: Implement `POST /api/threads` per PLAN.md FR-4: company is required and is created on the fly if the name is new; role title, role family, contact, motion, and JD URL are all optional. The thread starts at stage `outreach`, status `open`, nudge zero, with `stage_entered_at` set. Test creating a thread from a bare company name, from an existing company id, and with a contact attached.

## 15. Thread read endpoints
Goal: A list view and a detail view that carry everything the UI needs.
Description: Implement `GET /api/threads` with filters for status, stage, motion, and role family, and `GET /api/threads/{id}` returning the thread plus its company, contact, ordered touch history, and stage event history — enough for the thread page to render without follow-up requests. Include the derived ghost-suggested flag and days-in-stage. Test both endpoints against a seeded thread with several touches.

## 16. Log-touch endpoint
Goal: Logging a touch records history and updates the thread's follow-up state in one call.
Description: Implement `POST /api/threads/{id}/touches` taking kind, direction, channel, date (defaulting to today), and a note. The handler appends the touch row and applies the cadence engine to update `next_follow_up_date` and `nudge_number`, honouring `follow_up_pinned`. Test that an outbound touch sets the expected date, an inbound touch clears it, and a pinned thread's date is untouched.

## 17. Manual follow-up date and snooze
Goal: The user can override or defer a follow-up date, and the override sticks.
Description: Implement `PATCH /api/threads/{id}/follow-up` for setting an explicit date (which sets `follow_up_pinned` to true, per PLAN.md FR-8) and `POST /api/threads/{id}/snooze` for pushing the date out by a chosen interval in business days. Snoozing should not advance the nudge number. Test that a pinned date survives a later outbound touch and that snooze skips weekends.

## 18. Stage transitions and terminal states
Goal: Stage changes are recorded as events and can move forward, backward, or to a terminal state.
Description: Implement `POST /api/threads/{id}/stage` accepting a target stage or a terminal status (`rejected`, `ghosted`, `withdrawn`, `closed`), writing a `stage_event` row, updating `thread.stage` or `thread.status`, and refreshing `stage_entered_at` and `closed_at`. Forward skips and backward corrections are both allowed, per PLAN.md FR-13. Test a normal advance, a referral jump from outreach straight to screen, a backward correction, and closing as rejected.

---

## Digest, funnel, and targets

## 19. Digest endpoint
Goal: One endpoint returns everything the home page shows.
Description: Implement `GET /api/digest` returning four groups per PLAN.md FR-12 — overdue follow-ups ranked by days overdue then stage, due today, at-risk threads (more than the configured 8 days in the same stage), and the live conversation count. Each row carries the thread id, company, contact, stage, and days overdue so the UI can act in place. Test with a seeded set of threads spanning overdue, due-today, future, at-risk, and closed.

## 20. Daily quota progress endpoint
Goal: Answer "have I done enough today?" from touch history alone.
Description: Implement `GET /api/quotas` that counts today's touches by category — cold outreach sent, warm intro requests sent, cold applications submitted, referral asks made — against the daily quotas in `config.yaml`, returning count, target, and remaining for each. All numbers derive from the `touch` and `thread` tables; do not add a counters table. Test against a seeded day of mixed touches and a day with none.

## 21. Campaign targets endpoint
Goal: Show cumulative progress toward the campaign totals and their deadlines.
Description: Implement `GET /api/targets` returning, for each campaign target in `config.yaml` (connections, warm outreach, cold applications, screens, interviews, offers), the cumulative count, the target, the deadline, and whether it is an input or an outcome. Input counts come from touches, outcome counts from `stage_event` rows reaching that stage. Test the input and outcome counting paths separately.

## 22. Funnel endpoint
Goal: Stage counts and conversion rates, sliceable and windowed.
Description: Implement `GET /api/funnel` returning counts for each of the five stages and stage-to-stage conversion rates, with query parameters for motion, role family, and time window (today, 7d, 30d, all), per PLAN.md FR-14. Counts should come from `stage_event` history so that a thread which passed through a stage still counts even after moving on. Test an unfiltered funnel, one sliced by motion, and one windowed to 7 days.

---

## Import

## 23. Settle the two importer open questions
Goal: A written decision on campaign window and bare-contact handling, recorded in the repo.
Description: PLAN.md §9 leaves two questions the importer cannot proceed without: whether the 60/60/100 campaign totals reset to a new window or carry forward with new deadlines (the 8/17 and 8/28 deadlines have passed), and whether the ~25 name-only rows in `docs/reference/bottom-up.csv` import as bare contacts with no thread or are left out. Decide both with the user, record the decision and reasoning in PLAN.md §9 as resolved, and update the campaign deadlines in `config.yaml` accordingly. No code beyond the config edit.

## 24. CSV import preview
Goal: Upload a CSV and see exactly what would be created, without writing anything.
Description: Implement `POST /api/import/preview` accepting a CSV upload and a column mapping, and returning the rows that would become companies, contacts, and threads, plus a per-row list of problems — unparseable dates, unknown enum values, missing company. Handle the real shapes in `docs/reference/bottom-up.csv` (headers plus trailing junk columns) and `docs/reference/top-down.csv` (a two-block sheet whose right-hand block is an agency list, not companies). Test against both real files checked into the repo.

## 25. CSV import commit
Goal: Confirming a previewed import writes the rows and reports what was skipped.
Description: Implement `POST /api/import/commit` that takes the same CSV and mapping, applies the import in a single transaction, and returns counts created per table alongside the list of rejected rows with reasons — bad rows are reported, never silently dropped, per PLAN.md FR-6. Match on company name and contact name to avoid duplicating on a re-run. Test a clean import, a re-run producing no duplicates, and an import with several bad rows.

---

## Frontend

## 26. Frontend scaffold
Goal: A React + Vite + TypeScript app that starts and talks to the API.
Description: Create `frontend/` with Vite, TypeScript, and a router, a typed API client module pointing at the FastAPI dev server via a proxy, and a shell layout with navigation for Digest, Threads, Funnel, and Corpus. Render one page that calls `/api/health` and displays the result, to prove the wiring end to end. Include the frontend run instructions in the README.

## 27. One-command dev runner
Goal: `make dev` (or one script) brings up backend and frontend together.
Description: Add a Makefile or shell script that runs Alembic migrations, starts uvicorn with reload, and starts the Vite dev server, with output from both streamed to one terminal and a clean shutdown on Ctrl-C. Per PLAN.md FR-3 there must be no container and no external service. Document it as the single entry point in the README and confirm it works from a clean checkout.

## 28. Digest home page
Goal: The app opens on the list of what to do today.
Description: Build the digest page at `/` consuming `GET /api/digest` and rendering the four sections — overdue, due today, at risk, and today's quota progress with the live conversation count. Rows show company, contact, stage, and days overdue; keep it a plain scannable list rather than cards. Actions come in the next task; this one renders and handles the empty and loading states.

## 29. In-place row actions on the digest
Goal: Log, snooze, advance, or close a thread without leaving the digest.
Description: Add the four row actions to the digest rows, each hitting the endpoint built earlier (log touch, snooze, stage change, close) and optimistically updating the row in place. Logging a touch should take one click plus at most a kind and a note — PLAN.md §8 treats "log requires navigating to the thread first" as a bug. Include the ghost-suggested prompt on rows that have hit three unanswered nudges.

## 30. Quick-add thread form
Goal: Add a new pursuit in under 15 seconds.
Description: Build the quick-add form reachable from anywhere in the app via a persistent control, with company as the only required field and role, role family, contact, motion, and JD URL optional. Remember the last-used motion and role family as defaults for the next add, and keep focus and keyboard flow tight enough to complete without the mouse. Submit posts to the quick-add endpoint and lands the user back where they were.

## 31. Thread detail page
Goal: One page shows a thread's full history so a follow-up can be written from it.
Description: Build `/threads/:id` rendering the company, contact, role, stage, current follow-up date and nudge count, plus a chronological timeline merging touches and stage events. Include the log-touch control, the manual follow-up date picker, snooze, and stage change inline on the page. Per PLAN.md US-10 the goal is writing a follow-up without reconstructing context from an inbox.

## 32. Threads list and company page
Goal: Browse the pipeline and see everything tied to one company.
Description: Build a threads list with filters for status, stage, motion, and role family over `GET /api/threads`, and a company page showing the company's details, its contacts, and its threads with their current stages. Both link into the thread detail page. Keep both read-only apart from the shared log-touch control.

## 33. Funnel and targets page
Goal: See the funnel, the daily quotas, and campaign progress on one screen.
Description: Build a page rendering the five-stage funnel with conversion rates and controls for the motion, role family, and time-window slices, alongside the daily quota bars and the campaign target bars with their deadlines. Distinguish input targets from outcome targets visually — outcomes are tracked but are never a number the user can fail, per PLAN.md FR-15. Consume the funnel, quotas, and targets endpoints.

## 34. Bulk outreach mode
Goal: Ten cold outreaches are ten rows in one screen, not ten form submissions.
Description: Build a bulk-entry screen with a grid of rows sharing a touch kind, channel, and date, where each row needs only a company and optionally a contact and role. Submitting creates or matches each company, creates the thread, and logs the outbound touch for every row in one request, reporting per-row failures without discarding the successful rows. This is countermeasure 6 in PLAN.md §8.

---

## Corpus and agent access

## 35. Corpus directory structure and conventions
Goal: The About Me corpus exists as markdown with a documented convention.
Description: Create `corpus/` with the seven subdirectories from PLAN.md FR-16 (`resume/`, `experience/`, `projects/`, `answers/`, `stories/`, `facts/`, `strategy/`), each with a README explaining what belongs there and a template file showing the YAML frontmatter (`title`, `tags`, `updated`). Seed `strategy/` with the agency and community list and the healthy-signal criteria noted in PLAN.md §1.1, which are deliberately files rather than tables. No app code in this task.

## 36. Corpus API
Goal: The app can list, read, and search the corpus straight from the filesystem.
Description: Implement `GET /api/corpus` returning the file tree with parsed frontmatter, `GET /api/corpus/{path}` returning one file's content, and `GET /api/corpus/search?q=` doing a case-insensitive content and tag match across files. Reads happen on request with no index table, per PLAN.md FR-17, and path handling must reject traversal outside the corpus directory. Test listing, reading, search hits and misses, and a traversal attempt.

## 37. Corpus browser page
Goal: Browse and copy corpus sections while an application form is open in the next tab.
Description: Build a corpus page with the directory tree on one side, the rendered markdown on the other, a search box over the search endpoint, and a copy button on every heading section that puts that section's raw markdown on the clipboard. Optimise for reading and copying, not editing — editing happens in the user's editor against the repo files.

## 38. `SCHEMA.md` and saved queries for agents
Goal: An agent can query the database usefully without introspecting it.
Description: Write `SCHEMA.md` documenting the five tables, their columns, the enum values, and the design notes an agent needs (one pending follow-up per thread, stage history in events, cadence in config). Add a `queries/` directory with saved, commented SQL for the four cases named in PLAN.md FR-19: due follow-ups, live pipeline, funnel this week, and at-risk threads. Verify each query runs against a seeded database and returns the expected shape.

## 39. Seed and demo data fixture
Goal: A single command fills a scratch database with realistic data for testing and demos.
Description: Add a script that creates a throwaway SQLite file populated with companies, contacts, and threads spread across all five stages, with touch histories that produce overdue, due-today, at-risk, and ghost-suggested rows. Reuse it as a pytest fixture so the digest, funnel, and target tests share one realistic dataset instead of each seeding its own. Keep it deterministic — fixed dates relative to a passed-in "today", no randomness.

## 40. Two-week field audit
Goal: Delete the fields that real use proved nobody fills.
Description: Two weeks after the app is in daily use, query the database for the fill rate of every optional column and every corpus directory, and list what is still empty. Remove the unused fields from the models, forms, and migrations rather than waiting for discipline to improve — PLAN.md §8 calls unfilled fields design errors, not features awaiting effort. Deliver the fill-rate numbers alongside the removals so the decision is legible later.
