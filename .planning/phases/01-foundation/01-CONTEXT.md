# Phase 1: Foundation - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Project scaffold, SQLite data model, FSRS scheduling engine, YAML question loading. This phase delivers the data and scheduling infrastructure — cards can be loaded from YAML files, stored in SQLite, and scheduled by FSRS. No quiz UX, no gamification, no AI. Just the foundation everything else builds on.

</domain>

<decisions>
## Implementation Decisions

### Question YAML Schema
- IDs use slug-style format: `k8s-pod-lifecycle-001` — human-readable, topic and sequence visible at a glance
- Shared base schema with type-specific fields: all questions have `id`, `type`, `topic`, `tier`, `tags`; each type adds its own fields (flashcard adds `front`/`back`; command-fill adds `command`/`accept_partial`; scenario and explain-concept have their own type-specific fields)
- One YAML file per topic: `kubernetes.yaml`, `terraform.yaml`, etc. — new topic = drop one file
- Version tracking via `version_tag` (e.g. `k8s-1.29`) + `last_verified` (e.g. `2026-01-01`) — explicit, human-editable

### Data and Config Locations
- All data lives under `~/.hackmyskills/` — one folder, easy to find and back up
- Database at `~/.hackmyskills/data.db`
- Config at `~/.hackmyskills/config.toml`
- User content (YAML question files) at `~/.hackmyskills/content/`
- First run auto-initializes silently: creates directory structure, copies bundled questions, initializes DB — no setup wizard

### CLI Behavior
- `hms` with no args shows a status dashboard: streak, cards due today, next session estimate
- Version format: semver starting at `0.1.0`
- Errors displayed as Rich styled error boxes (red panel with message + suggestion)
- Flat command structure: `hms quiz`, `hms stats`, `hms generate`, `hms daemon start` — all top-level, fast to type

### Dev Workflow
- Installation: `pip install -e .` in a virtual environment — `hms` command works globally in the venv
- Testing: pytest with a temp directory fixture — each test gets a fresh isolated `~/.hackmyskills-test/` dir, no touching real user data
- Python minimum: 3.12+
- Build backend: Hatchling (pyproject.toml)

### Claude's Discretion
- Internal package/module structure (src layout vs flat)
- Exact Peewee model field names beyond what's implied by schema
- Error exit codes
- Compression or encryption of the SQLite DB (not needed for Phase 1)

</decisions>

<specifics>
## Specific Ideas

- The status dashboard on `hms` (no args) should feel motivating — like checking your Duolingo streak. Show what's waiting, not just a help menu.
- Question IDs should be readable in YAML without decoding: `k8s-pod-lifecycle-001` tells you topic + sequence at a glance.
- The content directory (`~/.hackmyskills/content/`) is designed to be user-editable — dropping a YAML file there should "just work" (even though the import command comes in Phase 6).

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet — greenfield project

### Established Patterns
- None yet — this phase establishes the patterns

### Integration Points
- `~/.hackmyskills/data.db` — all subsequent phases read/write here
- `~/.hackmyskills/content/*.yaml` — Phase 6 import command and Phase 5 AI generation target this directory
- `~/.hackmyskills/config.toml` — Phase 4 daemon config lives here (quiet hours, intervals)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-03-13*
