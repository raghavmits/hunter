1;2A1;2A1;2A1;2B1;2B1;2B1;2A# Job Search Tracker

Status: draft
Owner: Raghav (single user)
Last updated: 2026-08-20

---

## What it is

A local, single-user tool for tracking job-search contacts and companies.
`tracker.html` — one static HTML file at the repo root, opened directly
in a browser. Two tabs, Contacts and Companies, each an editable table,
linked to each other. Data lives in the browser's `localStorage`. No
backend, no database, no build step.

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
        text hiringCompanies "free text, nullable — companies this contact might refer me into, not necessarily their employer"
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
    }
```

A contact optionally links to one company via `companyId`. A company's
Contact(s) list isn't stored — it's computed by filtering contacts for a
matching `companyId`. Deleting a company clears a linked contact's
`companyId`; it doesn't delete the contact.
