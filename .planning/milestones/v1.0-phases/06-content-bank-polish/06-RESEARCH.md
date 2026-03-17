# Phase 6: Content Bank + Polish - Research

**Researched:** 2026-03-16
**Domain:** YAML content authoring, CLI command extension, config file generation, content validation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Mix of concept-focused and tool-focused subtopics: core concepts first, then GitHub Actions as primary CI/CD tool example
- 3 new YAML files needed: `cicd.yaml`, `bash.yaml`, `aws.yaml`
- Existing `kubernetes.yaml` and `terraform.yaml` must be audited and expanded to meet 30/10/5 minimums per tier
- L2 (application) and L3 (scenario) cards should be based on real-world production incidents -- e.g., "pod OOMKilled, here are the logs, diagnose" -- practical and realistic
- AWS scope covers both core services (EC2, VPC, S3, IAM, Route53, ELB) and DevOps-specific services (ECS, ECR, CodePipeline, CloudFormation, CloudWatch)
- `hms topics` compact format: topic name + total card count + highest unlocked tier; shows ALL discovered topics from loaded YAML files
- `hms import` all-or-nothing validation: reject entire file if any question fails schema validation; run duplicate detection; block import if duplicates found
- Config.toml created on first run by `ensure_initialized()` with all settings included, organized in sections: `[general]`, `[daemon]`, `[quiet_hours]`
- Friendly + practical inline comments for every setting

### Claude's Discretion

- Exact subtopic distribution per topic (how many K8s networking vs storage vs RBAC questions)
- Import destination strategy (copy vs merge)
- Config.toml section ordering and exact comment wording
- Rich output formatting for `hms topics` (table vs panel)
- Whether `hms import` reports a summary after successful import

### Deferred Ideas (OUT OF SCOPE)

- `hms update-content` command for downloading new question packs from URL -- noted in Phase 5
- Community question packs / import from URL -- v2 requirement (EXT-V2-02)
- Non-DevOps skill tracks -- v2 requirement (EXT-V2-01)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONT-01 | Curated question bank ships with >=30 L1 cards per topic for: Kubernetes, Terraform, CI/CD, bash, AWS | YAML content authoring patterns documented; gap analysis shows K8s needs +26 L1, TF needs +25 L1, CI/CD/bash/AWS need 30+ L1 each from scratch |
| CONT-02 | Each topic has at least 10 L2 (application) cards | Existing schema supports L2 tier; scenario and command-fill types suitable for application-level |
| CONT-03 | Each topic has at least 5 L3 (scenario) cards | Existing schema supports L3 tier; scenario type with real-world incident patterns documented |
| CONT-04 | All curated questions have version_tag and last_verified date | Both fields are REQUIRED_BASE_FIELDS in loader.py; already enforced at load time |
| CONT-05 | `hms topics` lists available topics with card counts and unlock status | `get_unlocked_tiers_per_topic()` and `load_all_questions()` provide all needed data; Typer command pattern documented |
| EXT-01 | New topics added by dropping YAML file into content directory -- no code changes | `load_all_questions()` globs `*.yaml` in content dir; `_sync_cards_from_yaml()` creates Card rows automatically; already works by design |
| EXT-02 | Config file (config.toml) is human-readable and documented inline | `_DEFAULT_CONFIG_TOML` template in init.py needs expansion; DEFAULT_CONFIG in config.py defines all settings |
| EXT-03 | `hms import <file.yaml>` validates and imports a question file into the active bank | `validate_content_dir()` and `find_duplicates()` provide validation; copy-to-content-dir + `_sync_cards_from_yaml()` provides import |
</phase_requirements>

---

## Summary

Phase 6 is primarily a content authoring phase with two CLI commands (`hms topics`, `hms import`) and a config.toml polish task. The codebase already has all the infrastructure needed: YAML schema validation in `loader.py`, duplicate detection in `validation.py`, topic/tier discovery in `gamification.py`, and the Typer CLI framework in `cli.py`. No new libraries are required.

The largest effort is creating 225+ curated DevOps questions across 5 topics (5 files, each needing 30+ L1, 10+ L2, 5+ L3 cards). The existing `kubernetes.yaml` (6 cards) and `terraform.yaml` (6 cards) need expansion from 6 to 45+ cards each. Three new files (`cicd.yaml`, `bash.yaml`, `aws.yaml`) must be created from scratch.

The CLI work is straightforward: `hms topics` aggregates data already available via existing functions, and `hms import` composes existing validation + file-copy + card-sync operations. The config.toml polish replaces the minimal `_DEFAULT_CONFIG_TOML` string with a fully documented template covering all settings from `DEFAULT_CONFIG`.

**Primary recommendation:** Structure plans as content-first (YAML authoring) then code (CLI commands + config polish). Content authoring is the bulk of the work and can be validated independently using `hms validate-content`.

---

## Standard Stack

### Core (already installed, no changes)

| Library | Version | Purpose | Phase 6 Usage |
|---------|---------|---------|---------------|
| typer | >=0.12.0 | CLI framework | `hms topics` and `hms import` commands |
| rich | >=13.0 | Terminal UI | Table/Panel output for `hms topics` |
| pyyaml | >=6.0 | YAML parsing | Content validation on import |
| peewee | >=4.0.1 | SQLite ORM | Card row creation on import |

### No New Dependencies

Phase 6 requires zero new packages. All content authoring uses existing YAML schema. All CLI commands use existing Typer/Rich patterns. All validation uses existing `validation.py`.

---

## Architecture Patterns

### Existing Content Discovery Flow

```
ensure_initialized()
  -> _copy_bundled_content(content_dir)    # copies hms/content/*.yaml to ~/.hackmyskills/content/
  -> _sync_cards_from_yaml(content_dir)    # creates Card rows for new question IDs
  -> load_all_questions(content_dir)       # globs *.yaml, validates each question
```

This flow means: dropping a valid YAML file into `~/.hackmyskills/content/` and running any `hms` command will automatically discover and sync it. EXT-01 is already architected -- it just needs verification.

### Question YAML Schema (reference)

```yaml
questions:
  - id: k8s-pod-lifecycle-001          # {topic_prefix}-{subtopic}-{number}
    type: flashcard                     # flashcard | scenario | command-fill | explain-concept
    topic: kubernetes                   # matches the filename stem
    tier: L1                            # L1 (recall) | L2 (application) | L3 (scenario)
    tags: [pods, lifecycle]             # list of topic-relative tags
    version_tag: k8s-1.29              # tool/platform version this applies to
    last_verified: "2026-01-01"        # ISO date of last accuracy check
    front: "Question text"             # type-specific fields vary
    back: "Answer text"
```

Required base fields (enforced by `validate_question()`):
- `id`, `type`, `topic`, `tier`, `tags`, `version_tag`, `last_verified`

Type-specific required fields:
- flashcard: `front`, `back`
- command-fill: `prompt`, `command`, `accept_partial`
- scenario: `situation`, `question`, `answer`, `explanation`
- explain-concept: `concept`, `model_answer`

### ID Naming Convention

Pattern: `{prefix}-{subtopic}-{type_hint}-{number}`

| Topic | Prefix | Examples |
|-------|--------|----------|
| kubernetes | k8s | `k8s-pod-lifecycle-001`, `k8s-svc-types-001` |
| terraform | tf | `tf-init-001`, `tf-state-001` |
| cicd | cicd | `cicd-gh-actions-workflow-001` |
| bash | bash | `bash-redirect-001`, `bash-awk-001` |
| aws | aws | `aws-s3-bucket-001`, `aws-iam-policy-001` |

### CLI Command Pattern (established)

```python
@app.command()
def topics() -> None:
    """List available topics with card counts and unlock status."""
    from hms.init import ensure_initialized
    ensure_initialized()
    # ... implementation with Rich table/panel output
```

Key conventions:
- Lazy imports inside command function body
- `ensure_initialized()` called first
- Rich Console for output (imported at module level)
- Typer decorators for argument/option parsing

### Typer File Argument Pattern

For `hms import <file.yaml>`:

```python
@app.command("import")
def import_file(
    file: Path = typer.Argument(..., help="Path to a YAML question file", exists=True),
) -> None:
    """Validate and import a question file into the active bank."""
    from hms.init import ensure_initialized
    ensure_initialized()
    # validate, check duplicates, copy, sync
```

Note: `import` is a Python keyword. Use `import_file` as the function name with `@app.command("import")` to register the CLI command name.

### Import Strategy: Copy File

Recommended approach (Claude's discretion area): **copy the entire file** to `~/.hackmyskills/content/` rather than merging into existing topic files.

Rationale:
- Simpler implementation (shutil.copy2)
- Preserves user's file as-is for traceability
- `load_all_questions()` already globs all `*.yaml` files -- multiple files per topic work fine
- If duplicate detection passes, the file is safe to add alongside existing ones
- Avoids YAML write/merge complexity and potential data corruption

### Config.toml Template Pattern

Current `_DEFAULT_CONFIG_TOML` in `init.py` is minimal (4 settings, 7 lines). Phase 6 expands it to cover all settings from `DEFAULT_CONFIG` with inline comments.

```toml
# HackMySkills Configuration
# Edit these settings to customize your experience.

[general]
# Maximum number of new cards introduced per day.
# Higher values mean faster progress but more daily work.
daily_cap = 25

[daemon]
# Minutes between interrupt notifications during work hours.
interval_minutes = 90

# Work hours — daemon only sends notifications during this window.
work_hours_start = "09:00"
work_hours_end = "21:00"

# Separate daily cap for interrupt-mode mini-sessions.
# Typically lower than general daily_cap since interrupts are 1 card each.
daily_cap = 10

[quiet_hours]
# No notifications before start or after end.
start = "09:00"
end = "21:00"
```

The template must stay in sync with `DEFAULT_CONFIG` in `config.py`. The `load_config()` function reads the TOML and merges over defaults, so all keys in `DEFAULT_CONFIG` should appear in the template.

### Anti-Patterns to Avoid

- **Don't merge YAML files during import:** Manipulating YAML structure risks data loss. Copy the file intact.
- **Don't validate against the DB for import:** Use `validate_content_dir()` which checks against all YAML files in the content directory. Don't query Card table for duplicate detection -- use the file-level `find_duplicates()`.
- **Don't add new dependencies:** Everything needed is already installed.
- **Don't break the existing `validate-content` command:** It must continue to work after adding new content files.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema validation | Custom validation logic for import | `validation.validate_content_dir()` | Already handles all question types, reports errors with file/ID context |
| Duplicate detection | String matching or hash-based dedup | `validation.find_duplicates()` | Jaccard similarity at 70% threshold already implemented and tested |
| Topic discovery | Manual topic list or enum | `get_unlocked_tiers_per_topic()` from gamification.py | Already queries Card table for distinct topics with unlock status |
| Card counting | Custom SQL queries | `Card.select().where(Card.topic == t).count()` | Peewee ORM already used this way in `_render_stats_panel()` |
| YAML writing | Custom YAML serialization | `shutil.copy2()` for import | Don't write YAML programmatically -- copy the user's file as-is |

**Key insight:** Phase 6 is primarily a composition phase. Nearly every code operation chains existing functions. The main new work is content authoring (YAML) and two thin CLI command wrappers.

---

## Common Pitfalls

### Pitfall 1: Config.toml Key Mismatch with DEFAULT_CONFIG

**What goes wrong:** The documented config.toml template has different key names or structure than `DEFAULT_CONFIG` in `config.py`, causing `load_config()` to silently ignore settings.
**Why it happens:** `DEFAULT_CONFIG` has a flat `daily_cap` at root level plus a nested `daemon.daily_cap`. The TOML template must mirror this exact structure.
**How to avoid:** After writing the template, verify that `tomllib.loads(template_string)` produces a dict whose keys are a superset of `DEFAULT_CONFIG`.
**Warning signs:** Tests pass but daemon uses wrong interval or daily cap.

### Pitfall 2: Duplicate Detection Across Import + Existing Content

**What goes wrong:** `hms import` validates the import file in isolation but doesn't check for duplicates against existing content already in `~/.hackmyskills/content/`.
**Why it happens:** `validate_content_dir()` checks a single directory. If you validate the import file alone, you miss cross-file duplicates.
**How to avoid:** Copy the import file to a temporary location inside the content dir (or a temp dir with existing content), then run `validate_content_dir()` on the combined set.
**Warning signs:** Import succeeds but `hms validate-content` subsequently reports duplicates.

### Pitfall 3: Content File Not Discovered After Import

**What goes wrong:** `hms import` copies the file but `hms quiz` doesn't show the new questions.
**Why it happens:** `_sync_cards_from_yaml()` must run to create Card rows. This happens in `ensure_initialized()` which runs on every command -- but only if the file lands in the right directory.
**How to avoid:** Import must copy to `HMS_HOME / "content"`, not to the bundled `src/hms/content/` directory.
**Warning signs:** Import reports success but `hms topics` shows 0 cards for the imported topic.

### Pitfall 4: YAML Content Quality -- Overlapping Questions

**What goes wrong:** When writing 225+ questions, similar questions across subtopics trigger the 70% Jaccard similarity threshold.
**Why it happens:** DevOps topics have overlapping vocabulary (e.g., "What command..." questions in both kubernetes and bash).
**How to avoid:** After writing each YAML file, run `hms validate-content` to detect cross-file overlaps. Use distinct vocabulary and specific tool references.
**Warning signs:** `validate-content` reports unexpected duplicate pairs.

### Pitfall 5: Import Keyword Collision in Python

**What goes wrong:** Using `def import(...)` as the command function name causes a SyntaxError because `import` is a Python reserved keyword.
**Why it happens:** The CLI command is `hms import` but the function can't be named `import`.
**How to avoid:** Name the function `import_file` and register it with `@app.command("import")`.
**Warning signs:** Immediate SyntaxError on module load.

### Pitfall 6: Existing quiet_hours Structure vs New Config Template

**What goes wrong:** Current `DEFAULT_CONFIG` has `quiet_hours.start`/`quiet_hours.end` at the top level AND `daemon.work_hours_start`/`daemon.work_hours_end` nested under daemon. The TOML template must preserve this dual structure for backward compatibility.
**Why it happens:** Phase 4 added daemon-specific settings alongside existing quiet_hours.
**How to avoid:** Keep both sections in the TOML template. Document which section controls what.
**Warning signs:** Config parsing silently uses defaults because user-edited values are in the wrong TOML section.

---

## Code Examples

### hms topics Command

```python
# Source: Modeled after _render_stats_panel() in cli.py
@app.command()
def topics() -> None:
    """List available topics with card counts and unlock status."""
    from hms.init import ensure_initialized
    ensure_initialized()

    from hms.gamification import get_unlocked_tiers_per_topic
    from hms.models import Card

    unlocked = get_unlocked_tiers_per_topic()
    topics_list = sorted(unlocked.keys())

    if not topics_list:
        console.print("[dim]No topics found. Add YAML files to your content directory.[/dim]")
        return

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("Topic")
    table.add_column("Cards", justify="right")
    table.add_column("Unlocked")

    for topic in topics_list:
        card_count = Card.select().where(Card.topic == topic).count()
        highest_tier = unlocked[topic][-1] if unlocked[topic] else "L1"
        table.add_row(topic, str(card_count), f"{highest_tier} unlocked")

    console.print(table)
```

### hms import Command

```python
# Source: Composed from existing validation.py + init.py patterns
@app.command("import")
def import_file(
    file: Path = typer.Argument(..., help="Path to YAML question file"),
) -> None:
    """Validate and import a question file into the active bank."""
    from hms.init import ensure_initialized
    import hms.config as _cfg
    ensure_initialized()

    file = Path(file)
    if not file.exists() or not file.suffix == ".yaml":
        console.print("[red]Error:[/red] File must be a .yaml file that exists.")
        raise typer.Exit(1)

    # Step 1: Validate the file in isolation (schema check)
    from hms.loader import load_questions
    try:
        questions = load_questions(file)
    except ValueError as exc:
        console.print(f"[red]Validation failed:[/red] {exc}")
        raise typer.Exit(1)

    # Step 2: Copy to content dir, run full validation (including duplicate check)
    import shutil
    content_dir = _cfg.HMS_HOME / "content"
    dest = content_dir / file.name
    if dest.exists():
        console.print(f"[red]Error:[/red] {file.name} already exists in content directory.")
        raise typer.Exit(1)

    shutil.copy2(file, dest)

    # Step 3: Validate the whole content directory (catches cross-file duplicates)
    from hms.validation import validate_content_dir
    result = validate_content_dir(content_dir)
    if not result.ok:
        dest.unlink()  # rollback: remove the copied file
        # Report errors
        for err in result.errors:
            console.print(f"  [red]X[/red] {err.question_id}: {err.message}")
        for dup in result.duplicates:
            console.print(f"  [yellow]![/yellow] Duplicate: {dup.id_a} <-> {dup.id_b}")
        raise typer.Exit(1)

    # Step 4: Sync cards to DB
    from hms.init import _sync_cards_from_yaml
    _sync_cards_from_yaml(content_dir)

    console.print(f"[green]OK[/green] Imported {len(questions)} questions from {file.name}.")
```

### Documented config.toml Template

```python
# Source: Expanded from init.py _DEFAULT_CONFIG_TOML
_DEFAULT_CONFIG_TOML = """\
# HackMySkills Configuration
# Edit these settings to customize your learning experience.

# Maximum number of new cards introduced per day.
# Higher values mean faster progress but more daily review work.
# Default: 25
daily_cap = 25

# Notification interval in minutes (legacy setting, prefer [daemon] section).
# Default: 90
interval_minutes = 90

[quiet_hours]
# Time window when the daemon will NOT send notifications.
# No notifications before 'start' or after 'end'.
# Use 24-hour format ("HH:MM").
# Default: start = "09:00", end = "21:00"
start = "09:00"
end = "21:00"

[daemon]
# Minutes between interrupt notifications during work hours.
# Default: 90
interval_minutes = 90

# Work hours window -- daemon only sends notifications during this time.
# Use 24-hour format ("HH:MM").
# Default: work_hours_start = "09:00", work_hours_end = "21:00"
work_hours_start = "09:00"
work_hours_end = "21:00"

# Separate daily cap for interrupt-mode mini-sessions.
# Typically lower than the general daily_cap since each interrupt is 1 card.
# Default: 10
daily_cap = 10
"""
```

---

## Gap Analysis: Content Counts

### Current State

| Topic | File Exists | L1 | L2 | L3 | Total |
|-------|-------------|-----|-----|-----|-------|
| kubernetes | Yes | 4 | 2 | 0 | 6 |
| terraform | Yes | 5 | 1 | 0 | 6 |
| cicd | No | 0 | 0 | 0 | 0 |
| bash | No | 0 | 0 | 0 | 0 |
| aws | No | 0 | 0 | 0 | 0 |

### Target State (minimum per requirements)

| Topic | L1 Needed | L2 Needed | L3 Needed | Total Min |
|-------|-----------|-----------|-----------|-----------|
| kubernetes | 30 (+26) | 10 (+8) | 5 (+5) | 45 (+39) |
| terraform | 30 (+25) | 10 (+9) | 5 (+5) | 45 (+39) |
| cicd | 30 (new) | 10 (new) | 5 (new) | 45 (new) |
| bash | 30 (new) | 10 (new) | 5 (new) | 45 (new) |
| aws | 30 (new) | 10 (new) | 5 (new) | 45 (new) |
| **TOTAL** | **150** | **50** | **25** | **225** |

### Recommended Subtopic Distribution (Claude's discretion)

**Kubernetes (k8s):**
- Pods/Containers: 8 L1, 2 L2, 1 L3
- Deployments/ReplicaSets: 5 L1, 2 L2, 1 L3
- Services/Networking: 5 L1, 2 L2, 1 L3
- ConfigMaps/Secrets: 4 L1, 1 L2, 1 L3
- Storage/PV/PVC: 4 L1, 1 L2, 1 L3
- RBAC/Security: 4 L1, 2 L2, 0 L3

**Terraform (tf):**
- Core workflow (init/plan/apply): 6 L1, 2 L2, 1 L3
- State management: 5 L1, 2 L2, 1 L3
- Variables/Outputs: 5 L1, 2 L2, 1 L3
- Modules: 5 L1, 2 L2, 1 L3
- Providers/Resources: 5 L1, 1 L2, 0 L3
- Backends/Workspaces: 4 L1, 1 L2, 1 L3

**CI/CD (cicd):**
- GitHub Actions basics: 8 L1, 2 L2, 1 L3
- Workflow syntax: 6 L1, 2 L2, 1 L3
- CI concepts (pipelines, stages): 6 L1, 2 L2, 1 L3
- Artifacts/Caching: 5 L1, 2 L2, 1 L3
- Deployment strategies: 5 L1, 2 L2, 1 L3

**Bash (bash):**
- Commands/Builtins: 8 L1, 2 L2, 1 L3
- Redirection/Pipes: 5 L1, 2 L2, 1 L3
- Text processing (grep/sed/awk): 6 L1, 2 L2, 1 L3
- Scripting (loops, conditionals): 6 L1, 2 L2, 1 L3
- Process management: 5 L1, 2 L2, 1 L3

**AWS (aws):**
- IAM (users, roles, policies): 6 L1, 2 L2, 1 L3
- EC2/VPC: 5 L1, 2 L2, 1 L3
- S3: 5 L1, 2 L2, 1 L3
- ECS/ECR: 5 L1, 1 L2, 1 L3
- CloudFormation/CloudWatch: 5 L1, 2 L2, 0 L3
- Route53/ELB: 4 L1, 1 L2, 1 L3

### Question Type Distribution Guideline

- L1 (recall): Mix of flashcard (60%) and command-fill (40%)
- L2 (application): Mix of scenario (50%), command-fill (30%), explain-concept (20%)
- L3 (scenario): Primarily scenario type (80%) with some explain-concept (20%), all based on realistic production incidents

### Version Tags

| Topic | version_tag Format | Example |
|-------|-------------------|---------|
| kubernetes | k8s-1.29 | k8s-1.29 |
| terraform | tf-1.7 | tf-1.7 |
| cicd | gh-actions-v4 | gh-actions-v4 |
| bash | bash-5.2 | bash-5.2 |
| aws | aws-2024 | aws-2024 |

All questions should use `last_verified: "2026-01-01"` as the baseline date.

---

## State of the Art

| Area | Current State | Phase 6 Change | Impact |
|------|---------------|----------------|--------|
| Content files | 2 files, 12 questions | 5 files, 225+ questions | Full DevOps coverage |
| CLI commands | quiz, stats, interrupt, validate-content, daemon | + topics, import | Complete CLI surface |
| Config template | 7-line minimal TOML | Fully documented with all settings | User self-service |
| Extensibility | Content dir exists but untested | Verified drop-in + import command | True extensibility |

**Nothing deprecated or outdated** -- all Phase 6 work builds on established patterns.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml (`[tool.pytest.ini_options]`) |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONT-01 | 30+ L1 cards per topic for 5 topics | unit | `pytest tests/test_content_bank.py::test_l1_count_per_topic -x` | No -- Wave 0 |
| CONT-02 | 10+ L2 cards per topic | unit | `pytest tests/test_content_bank.py::test_l2_count_per_topic -x` | No -- Wave 0 |
| CONT-03 | 5+ L3 cards per topic | unit | `pytest tests/test_content_bank.py::test_l3_count_per_topic -x` | No -- Wave 0 |
| CONT-04 | All questions have version_tag and last_verified | unit | `pytest tests/test_content_bank.py::test_metadata_fields -x` | No -- Wave 0 |
| CONT-05 | hms topics lists topics with counts and unlock status | unit | `pytest tests/test_cli.py::test_topics_command -x` | No -- Wave 0 |
| EXT-01 | Drop-in YAML discovery without code changes | integration | `pytest tests/test_content_bank.py::test_drop_in_yaml_discovery -x` | No -- Wave 0 |
| EXT-02 | Config.toml is human-readable with inline docs | unit | `pytest tests/test_init.py::test_config_toml_documented -x` | No -- Wave 0 |
| EXT-03 | hms import validates and imports a question file | unit | `pytest tests/test_cli.py::test_import_command -x` | No -- Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_content_bank.py` -- covers CONT-01 through CONT-04, EXT-01 (content count assertions, metadata checks, drop-in discovery)
- [ ] `tests/test_cli.py::test_topics_command` -- covers CONT-05 (new test in existing file)
- [ ] `tests/test_cli.py::test_import_command` -- covers EXT-03 (new test in existing file)
- [ ] `tests/test_cli.py::test_import_rejects_invalid` -- covers EXT-03 error path
- [ ] `tests/test_cli.py::test_import_rejects_duplicates` -- covers EXT-03 duplicate blocking
- [ ] `tests/test_init.py::test_config_toml_documented` -- covers EXT-02 (new test in existing file)

---

## Open Questions

1. **Config.toml backward compatibility on upgrade**
   - What we know: `_write_default_config()` only writes if file doesn't exist (`if not config_path.exists()`)
   - What's unclear: Existing users who already have a minimal config.toml won't get the new documented version
   - Recommendation: Accept this limitation for v1. Users can delete their config.toml to get the new template. Don't auto-migrate.

2. **Import file naming conflicts**
   - What we know: Import copies the file to content dir using the original filename
   - What's unclear: What if the user imports `kubernetes.yaml` when one already exists?
   - Recommendation: Check for filename collision before copy. Reject with clear error message suggesting rename.

3. **Cross-file duplicate detection performance**
   - What we know: `find_duplicates()` is O(n^2) with Jaccard similarity. With 225+ questions, this is ~25,000 comparisons.
   - What's unclear: Whether this causes noticeable delay on import
   - Recommendation: 25,000 string comparisons is trivially fast (< 1 second). No optimization needed for v1.

---

## Sources

### Primary (HIGH confidence)

- `src/hms/loader.py` -- REQUIRED_BASE_FIELDS, VALID_TYPES, VALID_TIERS, validate_question(), load_all_questions()
- `src/hms/validation.py` -- validate_content_dir(), find_duplicates(), DUPLICATE_THRESHOLD
- `src/hms/cli.py` -- Existing command patterns, _render_stats_panel() as reference for topics command
- `src/hms/config.py` -- DEFAULT_CONFIG structure, load_config() merge behavior
- `src/hms/init.py` -- ensure_initialized(), _sync_cards_from_yaml(), _write_default_config()
- `src/hms/gamification.py` -- get_unlocked_tiers_per_topic(), Card queries
- `src/hms/content/kubernetes.yaml` -- Reference YAML format (6 questions, 4 types)
- `src/hms/content/terraform.yaml` -- Reference YAML format (6 questions)
- `tests/conftest.py` -- hms_home fixture pattern for isolated testing
- `pyproject.toml` -- Package config, no new deps needed

### Secondary (MEDIUM confidence)

- Content subtopic distributions -- based on domain knowledge of DevOps curricula

### Tertiary (LOW confidence)

- None -- all findings verified against source code

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, all existing code verified
- Architecture: HIGH -- all patterns extracted from working codebase, commands follow established conventions
- Content schema: HIGH -- validated against loader.py source code
- Pitfalls: HIGH -- identified from actual code structure (config key mismatch, import keyword, duplicate detection scope)
- Content distribution: MEDIUM -- subtopic counts based on domain knowledge, exact numbers are Claude's discretion per CONTEXT.md

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (stable -- no external dependencies or fast-moving libraries)
