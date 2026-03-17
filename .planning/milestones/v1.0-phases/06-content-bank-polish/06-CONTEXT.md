# Phase 6: Content Bank + Polish - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Ship a complete curated DevOps question bank across 5 topics (Kubernetes, Terraform, CI/CD, bash, AWS) with 30+ L1, 10+ L2, 5+ L3 cards each. Add `hms topics` and `hms import` commands. Document config.toml with inline comments. The tool becomes fully extensible without code changes.

</domain>

<decisions>
## Implementation Decisions

### Content Coverage Strategy
- Mix of concept-focused and tool-focused subtopics: core concepts first, then GitHub Actions as primary CI/CD tool example
- 3 new YAML files needed: `cicd.yaml`, `bash.yaml`, `aws.yaml`
- Existing `kubernetes.yaml` and `terraform.yaml` must be audited and expanded to meet 30/10/5 minimums per tier
- L2 (application) and L3 (scenario) cards should be based on real-world production incidents — e.g., "pod OOMKilled, here are the logs, diagnose" — practical and realistic
- AWS scope covers both core services (EC2, VPC, S3, IAM, Route53, ELB) and DevOps-specific services (ECS, ECR, CodePipeline, CloudFormation, CloudWatch)

### hms topics Display
- Compact format: topic name + total card count + highest unlocked tier
- e.g., `kubernetes  45 cards  L2 unlocked`
- Shows ALL discovered topics from any loaded YAML file — user-added topics appear automatically
- Show highest unlocked tier only — no lock icons or tier breakdown, keep it clean

### hms import Behavior
- All-or-nothing validation: reject the entire file if any question fails schema validation
- Run duplicate detection against existing questions; block import if duplicates found (exact ID or >70% token overlap)
- Import destination: Claude's discretion on whether to copy file or merge into existing topic files
- Uses existing `validation.py` infrastructure (validate_question + find_duplicates)

### Config.toml Polish
- Documented config.toml created on first run by `ensure_initialized()`
- All settings included, organized in sections: `[general]`, `[daemon]`, `[quiet_hours]`
- Friendly + practical inline comments — e.g., `# How many new cards per day. Higher = faster but more tiring. Default: 25`
- Every setting explained with its purpose and default value

### Claude's Discretion
- Exact subtopic distribution per topic (how many K8s networking vs storage vs RBAC questions)
- Import destination strategy (copy vs merge)
- Config.toml section ordering and exact comment wording
- Rich output formatting for `hms topics` (table vs panel)
- Whether `hms import` reports a summary after successful import

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Question Schema & Validation
- `src/hms/loader.py` -- REQUIRED_BASE_FIELDS, VALID_TYPES, VALID_TIERS, VALID_SOURCES, TYPE_REQUIRED_FIELDS define the schema all content must conform to
- `src/hms/validation.py` -- validate_content_dir() and find_duplicates() for schema checks and duplicate detection
- `src/hms/content/kubernetes.yaml` -- Reference YAML format for all question types and ID naming convention

### CLI Structure
- `src/hms/cli.py` -- Existing CLI commands; `hms topics` and `hms import` to be added here
- `src/hms/cli.py:_render_stats_panel()` -- Pattern for per-topic data display using Rich tables

### Configuration
- `src/hms/config.py` -- DEFAULT_CONFIG dict, CONFIG_PATH, load_config() — config.toml generation must match these defaults
- `src/hms/init.py` -- ensure_initialized() — config.toml creation happens here on first run

### Content Loading
- `src/hms/loader.py:load_all_questions()` -- How content files are discovered (bundled vs user content dir)
- `src/hms/loader.py:get_bundled_content_files()` -- How bundled content is accessed via importlib.resources

### Gamification (for unlock status)
- `src/hms/gamification.py` -- get_unlocked_tiers_per_topic() used by `hms topics` to show unlock status

### Requirements
- `.planning/REQUIREMENTS.md` -- CONT-01 through CONT-05, EXT-01 through EXT-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `validation.validate_content_dir()`: Full schema + duplicate validation — reuse directly for `hms import` validation
- `validation.find_duplicates()`: Cross-file duplicate detection with Jaccard similarity — reuse for import blocking
- `loader.validate_question()`: Per-question schema validation with source field support already added
- `loader.load_all_questions()`: Discovers all YAML in content dir — reuse for `hms topics` card counting
- `gamification.get_unlocked_tiers_per_topic()`: Returns unlock status per topic — reuse for `hms topics` display
- `cli._render_stats_panel()`: Pattern for Rich table with per-topic data — similar pattern for `hms topics`

### Established Patterns
- Typer `@app.command()` for top-level commands with lazy imports
- Rich Console for terminal output (panels, tables)
- `ensure_initialized()` at command entry point
- Content stored as bundled YAML in `src/hms/content/` with fallback to `~/.hackmyskills/content/`
- Question ID format: `{topic}-{subtopic}-{type_hint}-{number}` (e.g., `k8s-pod-lifecycle-001`)

### Integration Points
- `cli.py`: Add `hms topics` and `hms import` commands
- `init.py`: Modify `ensure_initialized()` to write documented config.toml on first run
- `src/hms/content/`: Add `cicd.yaml`, `bash.yaml`, `aws.yaml`; expand `kubernetes.yaml`, `terraform.yaml`
- `config.py`: DEFAULT_CONFIG defines all settings — config.toml template must stay in sync

</code_context>

<specifics>
## Specific Ideas

- Content directory `~/.hackmyskills/content/` is designed to be user-editable — dropping a YAML file there should "just work" (established in Phase 1)
- User explicitly wants NO Claude API dependency for end users (Phase 5 decision)
- L3 scenarios should feel like real incident debugging — "here are the logs, what went wrong?" style
- CI/CD content should emphasize GitHub Actions as the primary tool since the project itself uses it

</specifics>

<deferred>
## Deferred Ideas

- `hms update-content` command for downloading new question packs from URL — noted in Phase 5
- Community question packs / import from URL — v2 requirement (EXT-V2-02)
- Non-DevOps skill tracks — v2 requirement (EXT-V2-01)

</deferred>

---

*Phase: 06-content-bank-polish*
*Context gathered: 2026-03-16*
