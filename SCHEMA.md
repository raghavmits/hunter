# Schema

`hunter.db` is a single SQLite file, five tables, checked into the repo (`AGENTS.md`). This document, plus `queries/`, is meant to be a working entry point for an agent — read this, run a saved query, don't introspect the database first (PLAN.md FR-19).

Verified against a freshly-migrated database (`sqlite3 hunter.db ".schema"`), not transcribed from the design doc — column names, types, and constraints below are the real thing.

## Two things that aren't obvious from the column list

**`thread.stage` and `thread.status` are separate columns, and only one is meaningful at a time.** `stage` (5 values: `outreach`, `replied`, `screen`, `interview`, `offer`) is the pipeline position, meaningful only while `status = 'open'`. `status` (`open` plus 4 terminal values: `rejected`, `ghosted`, `withdrawn`, `closed`) is whether the thread is still being pursued. A closed thread's `stage` column still holds whatever stage it was at when it closed ("rejected at screen" vs. "rejected at interview" is meaningful history), it just isn't the thing to filter on for "is this thread active." `stage_event.from_stage`/`to_stage` share one 9-value enum covering *both* `stage` and terminal `status` values, since a stage transition can end at either — a query joining `stage_event` needs to know a value like `'rejected'` there means a status, not a stage.

**Dates and datetimes mix UTC and local semantics, on purpose, and it matters for query correctness.** `stage_event.occurred_at` and `thread.stage_entered_at` are UTC instants (`datetime.now(UTC)` in the app). `touch.occurred_at` and `thread.next_follow_up_date` are **local** calendar dates (`date.today()`) — deliberately, since "did I do this today" and "when's my next follow-up" are local-calendar-day concepts, not UTC-instant ones. SQLite's `DATE('now')` returns the **UTC** date. Comparing it directly against `next_follow_up_date` (a local date) can be off by a day depending on the machine's UTC offset — see `queries/due_follow_ups.sql`'s own comment for how that query handles it.

## Tables

### `company`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `INTEGER` | PK |
| `name` | `VARCHAR` | not null |
| `url` | `VARCHAR` | nullable |
| `why_interested` | `TEXT` | nullable |
| `status` | `VARCHAR(9)` | not null. `watchlist \| active \| dormant \| closed` |
| `created_at` | `DATETIME` | not null, defaults to now |

### `contact`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `INTEGER` | PK |
| `company_id` | `INTEGER` | **nullable** — a contact can exist with no company (PLAN.md §7.3) |
| `full_name` | `VARCHAR` | not null |
| `title` | `VARCHAR` | nullable |
| `email` | `VARCHAR` | nullable |
| `linkedin_url` | `VARCHAR` | nullable |
| `warmth` | `VARCHAR(6)` | nullable. `cold \| warm \| strong` |
| `source` | `VARCHAR(16)` | nullable. `recruiter \| eng_manager \| friend \| family \| ex_colleague \| linkedin \| berkeley_iitk \| networking_event \| hackathon \| interviewed_at \| friend_of_friend` |
| `how_we_met` | `TEXT` | nullable |
| `notes` | `TEXT` | nullable |
| `created_at` | `DATETIME` | not null, defaults to now |

FK: `company_id → company.id`.

### `thread` — the unit of pursuit

One thread ≈ one row of the original bottom-up tracking sheet. Deliberately shallow — no join table to a separate "opportunity" concept; if three people at one company are worth pursuing separately, that's three threads sharing a `company_id` (PLAN.md §7.3).

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `INTEGER` | PK |
| `company_id` | `INTEGER` | not null |
| `contact_id` | `INTEGER` | **nullable** — cold applications have no person (PLAN.md §7.3) |
| `role_title` | `VARCHAR` | nullable |
| `role_family` | `VARCHAR(5)` | nullable. `FDE \| SWE \| MLE \| MTS \| OTHER` |
| `motion` | `VARCHAR(16)` | nullable. `cold_outreach \| warm_outreach \| cold_application` |
| `stage` | `VARCHAR(9)` | not null. `outreach \| replied \| screen \| interview \| offer` — see "stage vs status" above |
| `status` | `VARCHAR(9)` | not null. `open \| rejected \| ghosted \| withdrawn \| closed` |
| `stage_entered_at` | `DATETIME` | not null, UTC instant. Drives the at-risk flag (8 days in the same stage, `config.yaml`'s `at_risk_threshold_days`) |
| `next_follow_up_date` | `DATE` | nullable, **local** date. One pending follow-up per thread — the whole reminder model is this one column (PLAN.md §7.3) |
| `nudge_number` | `INTEGER` | not null. Consecutive unanswered outbound touches; resets to 0 on any inbound touch. 3+ suggests ghosting (never auto-closes) |
| `follow_up_pinned` | `BOOLEAN` | not null. Once true, cadence stops overwriting `next_follow_up_date` on the next touch — how a manually-set date (FR-8) survives |
| `referral_promised` | `BOOLEAN` | not null |
| `referral_submitted_at` | `DATE` | nullable, local date. Null until actually submitted |
| `jd_url` | `VARCHAR` | nullable |
| `notes` | `TEXT` | nullable |
| `created_at` | `DATETIME` | not null, defaults to now |
| `closed_at` | `DATETIME` | nullable. Set when `status` becomes terminal, cleared if the thread re-opens |

FK: `company_id → company.id`, `contact_id → contact.id`.
Index: `(status, next_follow_up_date)` — the digest's own query shape.

### `touch` — append-only

Every outreach action and every reply, one row each. No update path.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `INTEGER` | PK |
| `thread_id` | `INTEGER` | not null, `ON DELETE CASCADE` |
| `kind` | `VARCHAR(21)` | not null. `cold_outreach \| warm_intro_request \| referral_promised \| post_recruiter_call \| post_interview \| application_submitted \| long_term_nurture` — keys into `config.yaml`'s `cadence` map |
| `direction` | `VARCHAR(8)` | not null. `outbound \| inbound` |
| `channel` | `VARCHAR(9)` | not null. `email \| linkedin \| referral \| phone \| in_person \| portal \| other` |
| `occurred_at` | `DATE` | not null, **local** date |
| `note` | `TEXT` | nullable |
| `created_at` | `DATETIME` | not null, defaults to now — when the row was logged, not necessarily `occurred_at` (backdating is allowed) |

FK: `thread_id → thread.id`.

### `stage_event` — append-only

One row per stage/status transition. `thread.stage`/`status` are the current state; this table is the history conversion rates and time-in-stage are computed from (PLAN.md §7.3 — "stage history is events, not a column").

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `INTEGER` | PK |
| `thread_id` | `INTEGER` | not null, `ON DELETE CASCADE` |
| `from_stage` | `VARCHAR(9)` | nullable (null on a thread's first recorded event — #14 doesn't write one at creation). `outreach \| replied \| screen \| interview \| offer \| rejected \| ghosted \| withdrawn \| closed` |
| `to_stage` | `VARCHAR(9)` | not null. Same 9-value set as `from_stage` |
| `occurred_at` | `DATETIME` | not null, UTC instant |
| `note` | `TEXT` | nullable |

FK: `thread_id → thread.id`.

## What's deliberately not here

No `daily_stats` table — every number in the digest/quota/funnel/targets views derives from `touch` and `stage_event` at query time; a counter table is the fastest way to get two sources of truth that disagree. No `corpus_item` table — the markdown files under `corpus/` are the truth, not indexed into SQLite. No `cadence_rule` or `target` table — cadences, daily quotas, and campaign targets live in `config.yaml`; they move into the database the day there's a need for history of what a target used to be, not before. No join tables anywhere — three people worth pursuing at one company is three `thread` rows, not a join table with a role enum.

## Saved queries

`queries/` has one `.sql` file per FR-19 case — `due_follow_ups.sql`, `live_pipeline.sql`, `funnel_this_week.sql`, `at_risk_threads.sql`. Each is commented and runnable standalone: `sqlite3 hunter.db < queries/due_follow_ups.sql`.
