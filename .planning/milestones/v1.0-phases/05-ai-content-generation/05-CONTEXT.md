# Phase 5: AI Content Generation - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Tooling and conventions for generating new questions via Claude Code sessions, validating content quality, and detecting duplicates. End users never interact with AI directly — questions are curated by the maintainer and shipped through content updates. The `hms generate` stub is removed; a new `hms validate-content` command and CI script replace the original review workflow.

</domain>

<decisions>
## Implementation Decisions

### Generation Workflow
- No Claude API dependency for end users — questions are created by the maintainer in Claude Code sessions and shipped as bundled YAML in releases
- No `hms generate` or `hms review-generated` CLI commands — remove the existing `generate` stub from cli.py
- No separate generation script — Claude Code writes questions directly into existing content YAML files (kubernetes.yaml, terraform.yaml, etc.)
- Review happens in the git diff before committing — no staging area needed

### Content Tagging
- Add optional `source` field to the question schema: `source: ai` or `source: curated`
- Missing `source` field defaults to `curated` — no backfill required for existing questions
- Same ID pattern as existing questions: `{topic}-{subtopic}-{type_hint}-{number}` (e.g., `k8s-rbac-scenario-003`)

### Generation Quality Standards
- Each generation batch produces a mix of all 4 question types (flashcard, scenario, command-fill, explain-concept)
- Difficulty tier (L1/L2/L3) specified per generation request — not mixed automatically
- Create a `docs/content-generation-guide.md` template defining quality standards, tone, and tier difficulty expectations
- Claude Code reads the guide + existing YAML examples before generating new questions

### Validation Command
- New `hms validate-content` CLI command — runs schema validation + duplicate detection across all YAML content files
- Same logic also available as a standalone CI script for GitHub Actions (content change gate)
- Two entry points, one validation library

### Duplicate Detection
- Duplicates detected by: exact question ID match + text similarity (token overlap)
- Simple token overlap comparison — flag when >70% word overlap between question text fields
- No external NLP dependencies — pure Python string operations
- On detection: report warnings listing duplicate pairs with similarity scores
- Non-zero exit code for CI integration; developer decides resolution
- Comparison scope: all questions across all YAML files in the content directory

### Claude's Discretion
- Internal structure of the validation module
- Exact token normalization (lowercase, stemming, stop words)
- CI script implementation details
- Content generation guide formatting and examples

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Question Schema
- `src/hms/loader.py` -- REQUIRED_BASE_FIELDS, VALID_TYPES, VALID_TIERS, TYPE_REQUIRED_FIELDS define the schema that generated questions and validation must conform to
- `src/hms/content/kubernetes.yaml` -- Reference YAML format for all question types (flashcard, scenario, command-fill, explain-concept)

### CLI Patterns
- `src/hms/cli.py` -- Existing CLI structure with Typer; `generate` stub at line 183 to be removed; `validate-content` command to be added
- `src/hms/config.py` -- Configuration loading pattern

### Content Loading
- `src/hms/loader.py:load_all_questions()` -- How content files are discovered and loaded; validation runs at load time
- `src/hms/loader.py:validate_question()` -- Existing per-question validation; `source` field must be added as optional

### Requirements
- `.planning/REQUIREMENTS.md` -- AI-01 through AI-05 requirements (note: implementation approach differs from original spec per user decisions above)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `loader.validate_question()`: Existing schema validator — extend with `source` field support and use as foundation for `validate-content`
- `loader.load_all_questions()`: Already loads all YAML files from content dir — reuse for content-wide validation
- `loader.REQUIRED_BASE_FIELDS` / `TYPE_REQUIRED_FIELDS`: Schema definitions to extend

### Established Patterns
- Typer CLI with `@app.command()` decorators for top-level commands
- Rich console for terminal output (panels, tables)
- Lazy imports inside command functions for startup speed
- `ensure_initialized()` call at command entry for DB setup

### Integration Points
- `cli.py`: Add `validate-content` command, remove `generate` stub
- `loader.py`: Extend `validate_question()` to accept optional `source` field
- `pyproject.toml`: No new runtime dependencies needed (token overlap is pure Python)
- `.github/workflows/`: CI script for content validation on YAML changes (new workflow file)
- `docs/content-generation-guide.md`: New file — quality guide for Claude Code sessions

</code_context>

<specifics>
## Specific Ideas

- User explicitly wants NO Claude API dependency for end users — "no one needs Claude subscriptions for this tool"
- Generation happens through Claude Code conversations — the maintainer asks Claude Code to write questions, reviews in git diff, commits
- The content generation guide should define what makes a good question per tier: L1 = recall, L2 = application, L3 = scenario complexity

</specifics>

<deferred>
## Deferred Ideas

- `hms update-content` command for users to download new question packs from a URL or release — potential Phase 6 addition
- Local LLM integration (e.g., ollama) for user-facing generation without subscriptions — future consideration

</deferred>

---

*Phase: 05-ai-content-generation*
*Context gathered: 2026-03-16*
