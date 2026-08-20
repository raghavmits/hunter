# Job Search Tracker

Status: draft
Owner: Raghav (single user)
Last updated: 2026-08-20

---

## What it is

A local, single-user tool for tracking job-search contacts and companies.

**Target architecture:** FastAPI backend + PostgreSQL database (via SQLAlchemy +
Alembic), React + Vite + TypeScript frontend. Python tooling: `uv`, `pytest`,
`ruff`, `ty`. Runs entirely locally — no LLM dependency, no external services,
deterministic.

`tracker.html` at the repo root is a working prototype (localStorage, no build
step). It defines the UX and data model but will be replaced by the full-stack
implementation.

---

## Data model

The shape of the JSON object stored under one `localStorage` key.

```mermaid
erDiagram
    COMPANY ||--o{ CONTACT : "employs (contact.companyId)"

    CONTACT {
        string id PK
        string name
        string companyId FK "nullable — links to Company.id"
        string title "Role/Title, nullable"
        enum contactMode "LinkedIn|Email|Referral|Cold|Event/Conference, nullable"
        enum warmth "Cold|Warm|Hot|Referral Ready, nullable"
        date lastConnected "nullable"
        date nextFollowUp "nullable, manually set"
        enum status "Reached Out|No Response|Replied|Call Scheduled|Referred|Interviewing|Dead End, nullable"
        string[] hiringCompanies "nullable — company names this contact might refer me into; each name links to a Company record if one exists"
        text notes "nullable"
    }

    COMPANY {
        string id PK
        string name
        enum stage "Seed|Series A|Series B+|Public, nullable"
        enum interest "Low|Medium|High, nullable"
        enum industry "AI|Bio/Health|Energy|Manufacturing|Consumer|Enterprise, nullable"
        string role "the specific role being tracked here, free text, nullable"
        string url "nullable"
        string careersPage "nullable"
        text notes "nullable"
    }
```

A contact optionally links to one company via `companyId`. A company's
Contact(s) list isn't stored — it's computed by filtering contacts for a
matching `companyId`. Deleting a company clears a linked contact's
`companyId`; it doesn't delete the contact.
