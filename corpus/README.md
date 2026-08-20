# Corpus

Markdown files, one concern per file, with YAML frontmatter on every file:

```yaml
---
title: ""
tags: []
updated: ""
---
```

`updated` is an ISO date (`YYYY-MM-DD`).

This is a filesystem, not a database — no index table, no build step. FR-17 (#37) adds a browse/search UI in the app, but search is filesystem-backed against these files directly, not a separate index that can drift out of sync. FR-18 (#36) gives agents read-only access to this directory and the SQLite file directly from the repo — no write path in v1.

## Directories

| Directory | What belongs there |
| --- | --- |
| [`resume/`](resume/) | Current resume(s), markdown plus source/PDF |
| [`experience/`](experience/) | One file per role held — scope, impact, metrics |
| [`projects/`](projects/) | One file per project — problem, approach, stack, outcome |
| [`answers/`](answers/) | Standard application answers, one per question |
| [`stories/`](stories/) | STAR-format behavioral stories |
| [`facts/`](facts/) | Visa status, notice period, comp expectations, locations, links |
| [`strategy/`](strategy/) | Narrative work and search notes — not modeled as database rows on purpose (PLAN.md §1.1): a list this short is a markdown file, not a table |

Each directory has its own `README.md` (what belongs there) and `template.md` (frontmatter + section prompts to copy for a new file).
