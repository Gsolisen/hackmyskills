# Phase 1: Foundation - Research

**Researched:** 2026-03-13
**Domain:** Python CLI packaging, SQLite ORM, YAML loading, FSRS spaced-repetition scheduling
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Question IDs**: Slug-style format — `k8s-pod-lifecycle-001` (human-readable, topic + sequence visible)
- **YAML schema**: Shared base fields (`id`, `type`, `topic`, `tier`, `tags`, `version_tag`, `last_verified`) with type-specific fields per question type (flashcard: `front`/`back`; command-fill: `command`/`accept_partial`; scenario and explain-concept have their own type-specific fields)
- **One YAML file per topic**: `kubernetes.yaml`, `terraform.yaml`, etc.
- **Data location**: All user data under `~/.hackmyskills/` — DB at `~/.hackmyskills/data.db`, config at `~/.hackmyskills/config.toml`, YAML content at `~/.hackmyskills/content/`
- **First-run auto-init**: Creates directory structure, copies bundled questions, initializes DB silently — no setup wizard
- **CLI entry point**: `hms` command (flat structure: `hms quiz`, `hms stats`, `hms generate`, `hms daemon start`)
- **Default `hms` (no args)**: Shows status dashboard (streak, cards due today, next session estimate) — not a help menu
- **Error display**: Rich styled error boxes (red panel with message + suggestion)
- **Version format**: Semver starting at `0.1.0`
- **Install method**: `pip install -e .` in a virtual environment
- **Testing**: pytest with temp directory fixture — each test gets a fresh isolated directory, no touching real user data
- **Python minimum**: 3.12+
- **Build backend**: Hatchling (`pyproject.toml`)
- **Full stack**: Python 3.12 + Typer + Rich + `fsrs` 6.3.1 + Peewee 4.0/SQLite + anthropic SDK + desktop-notifier + APScheduler

### Claude's Discretion

- Internal package/module structure (src layout vs flat)
- Exact Peewee model field names beyond what the schema implies
- Error exit codes
- Compression or encryption of the SQLite DB (not needed for Phase 1)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FOUND-01 | Project scaffolded as a Python 3.12 CLI package installable via `pip install -e .` | Hatchling build backend + `[project.scripts]` entry point; `src/` layout pattern documented |
| FOUND-02 | SQLite database initialized at `~/.hackmyskills/data.db` on first run | Peewee 4.0.1 deferred init pattern with `db.init()` + `create_tables()` |
| FOUND-03 | Question bank loaded from YAML files in `~/.hackmyskills/content/` (or bundled) | PyYAML `safe_load` + `importlib.resources.files()` for bundled content |
| FOUND-04 | YAML question schema supports types: flashcard, scenario, command-fill, explain-concept | Type-discriminated schema with shared base + per-type fields; validated via Python dataclasses or manual checks |
| FOUND-05 | Each question has: id, type, topic, difficulty_tier (L1/L2/L3), tags, version_tag, last_verified | Mapped to Peewee model fields; YAML schema base section covers all |
| FOUND-06 | FSRS v6 scheduling engine wraps `fsrs` library — cards scheduled by due date | `fsrs` 6.3.1 (released 2026-03-10); `Scheduler`, `Card`, `Rating` classes; `review_card()` API |
| FOUND-07 | Review history persisted per card (rating, timestamp, FSRS state fields) | `ReviewLog.to_json()` serialized into a Peewee `TextField`; Card FSRS fields stored as individual columns or JSON blob |
</phase_requirements>

---

## Summary

This phase establishes the entire foundation of HackMySkills: a Python 3.12 CLI package installable with `pip install -e .`, a SQLite database for card state and review history, YAML loading for the question bank, and an FSRS v6 scheduling engine. All libraries in the locked stack are stable, current, and well-documented.

The `fsrs` library is at version 6.3.1 (released 2026-03-10) and implements FSRS-6, which adds two new parameters (21 total weights) for improved short-term review scheduling. `Card` and `ReviewLog` objects serialize to/from JSON natively, making SQLite storage straightforward. Peewee 4.0.1 (released 2026-03-01) is the current major version and works cleanly with SQLite via deferred initialization — essential because the DB path is only known at runtime from `~/.hackmyskills/data.db`. Typer 0.24.1 is current and provides the `hms` entry point, automatic `--help`, and a `CliRunner` for testing.

The key architectural challenge is the deferred database path. Peewee's `db.init()` pattern solves this cleanly: define `db = SqliteDatabase(None)` at module level, then call `db.init(path, pragmas=...)` during first-run initialization before any model operations. The `importlib.resources.files()` API (stable in Python 3.12+) handles bundled YAML content for the initial question bank without filesystem fragility.

**Primary recommendation:** Use `src/hms/` layout, Peewee deferred init for the runtime DB path, `fsrs` `Scheduler.review_card()` for scheduling, PyYAML `safe_load` for YAML, and `importlib.resources.files()` for bundled content.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| typer | 0.24.1 | CLI framework (entry points, subcommands, help) | Type-hint-first; ships with Rich integration; `CliRunner` for tests |
| rich | current (typer dep) | Terminal output, error panels, status dashboard | Locked decision; Typer depends on it |
| peewee | 4.0.1 | SQLite ORM — models, queries, migrations | Lightweight, no async complexity, deferred init support |
| fsrs | 6.3.1 | FSRS-6 spaced repetition scheduler | Locked decision; implements FSRS v6 algorithm |
| pyyaml | 6.x | YAML question file loading | Standard library for YAML in Python ecosystem |
| hatchling | 1.26+ | Build backend for pyproject.toml | Locked decision; modern, well-supported by PyPA |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x | Test framework | All unit and integration tests |
| tomllib | stdlib (3.11+) | config.toml reading | Built-in — no extra dependency needed |
| importlib.resources | stdlib (3.12) | Access bundled YAML content | Loading questions shipped inside the package |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Peewee | SQLAlchemy | SQLAlchemy is heavier, async-first options add complexity; Peewee fits this solo-CLI use case well |
| PyYAML | ruamel.yaml / strictyaml | ruamel preserves comments; strictyaml is safer but more restrictive. PyYAML `safe_load` is sufficient for trusted bundled content |
| Peewee deferred init | SQLite3 directly | Raw sqlite3 requires hand-rolling schema management; Peewee gives model definition, create_tables, and query ORM for free |

**Installation:**

```bash
pip install -e ".[dev]"
# pyproject.toml will pull: typer, rich, peewee, fsrs, pyyaml
# dev extras: pytest
```

---

## Architecture Patterns

### Recommended Project Structure

```
hackmyskills/
├── pyproject.toml           # Hatchling build, entry point hms
├── src/
│   └── hms/
│       ├── __init__.py
│       ├── cli.py           # typer app, all command definitions
│       ├── db.py            # Peewee db object (deferred), BaseModel
│       ├── models.py        # Card, ReviewHistory Peewee models
│       ├── loader.py        # YAML loading, validation, bundled content copy
│       ├── scheduler.py     # Thin wrapper around fsrs Scheduler
│       ├── init.py          # First-run setup: dirs, copy content, db.init(), create_tables()
│       ├── config.py        # Config reading via tomllib
│       └── content/         # Bundled question YAML files
│           ├── kubernetes.yaml
│           └── terraform.yaml
└── tests/
    ├── conftest.py          # hms_home fixture (tmp_path), monkeypatched DB
    ├── test_loader.py
    ├── test_scheduler.py
    ├── test_models.py
    └── test_cli.py
```

### Pattern 1: Deferred Peewee Database Initialization

**What:** Define the database object at module level with `None`, then call `db.init()` at first-run time once the runtime path is known.

**When to use:** Any time the DB path depends on runtime state (user home directory, env override in tests).

```python
# Source: https://docs.peewee-orm.com/en/latest/peewee/database.html
from peewee import SqliteDatabase, Model

db = SqliteDatabase(None)  # deferred — path unknown at import time

class BaseModel(Model):
    class Meta:
        database = db

# Called during first-run init:
def initialize_db(path: str) -> None:
    db.init(path, pragmas={
        "journal_mode": "wal",
        "cache_size": -16000,   # 16MB
        "foreign_keys": 1,
    })
    db.create_tables([Card, ReviewHistory], safe=True)
```

### Pattern 2: FSRS Review Workflow

**What:** Create a `Scheduler`, load a `Card` from its stored JSON, call `review_card()`, persist updated card + ReviewLog.

**When to use:** Every time a user submits a rating for a question.

```python
# Source: https://github.com/open-spaced-repetition/py-fsrs
from fsrs import Scheduler, Card, Rating

scheduler = Scheduler()

# On first review of a new card:
card = Card()

# After user rates:
card, review_log = scheduler.review_card(card, Rating.Good)

# Persist:
db_card.fsrs_state = card.to_json()
db_card.due = card.due
db_card.save()

ReviewHistory.create(
    card=db_card,
    rating=rating.value,
    reviewed_at=review_log.review_datetime,
    review_log_json=review_log.to_json(),
)
```

### Pattern 3: Bundled Content with importlib.resources

**What:** Ship starter YAML question files inside the package; copy them to `~/.hackmyskills/content/` on first run.

**When to use:** First-run auto-init — user gets a working question bank immediately.

```python
# Source: https://docs.python.org/3.12/library/importlib.resources.html
from importlib.resources import files
import shutil
from pathlib import Path

def copy_bundled_content(target_dir: Path) -> None:
    content_pkg = files("hms.content")
    for resource in content_pkg.iterdir():
        if resource.name.endswith(".yaml"):
            dest = target_dir / resource.name
            if not dest.exists():
                dest.write_bytes(resource.read_bytes())
```

### Pattern 4: Typer App with `hms` Entry Point

**What:** Single `typer.Typer()` app registered as the `hms` console script.

```python
# Source: https://typer.tiangolo.com/tutorial/package/
import typer

app = typer.Typer()

@app.callback(invoke_without_command=True)
def default(ctx: typer.Context):
    """HackMySkills — show status dashboard when no subcommand given."""
    if ctx.invoked_subcommand is None:
        show_dashboard()

@app.command()
def quiz():
    """Start a focused quiz session."""
    ...
```

**pyproject.toml entry point:**

```toml
[project.scripts]
hms = "hms.cli:app"
```

### Pattern 5: YAML Loading with Type Dispatch

**What:** Load a topic YAML file, validate the base fields, then dispatch to a type-specific validator/dataclass.

```python
# PyYAML safe_load — trusted content only
import yaml
from pathlib import Path

REQUIRED_BASE_FIELDS = {"id", "type", "topic", "tier", "tags", "version_tag", "last_verified"}
VALID_TYPES = {"flashcard", "scenario", "command-fill", "explain-concept"}

def load_questions(yaml_path: Path) -> list[dict]:
    with yaml_path.open() as f:
        data = yaml.safe_load(f)
    questions = data.get("questions", [])
    validated = []
    for q in questions:
        missing = REQUIRED_BASE_FIELDS - q.keys()
        if missing:
            raise ValueError(f"Question {q.get('id', '?')} missing fields: {missing}")
        if q["type"] not in VALID_TYPES:
            raise ValueError(f"Unknown type: {q['type']}")
        validated.append(q)
    return validated
```

### Anti-Patterns to Avoid

- **Hardcoding the DB path at module level:** `SqliteDatabase("~/.hackmyskills/data.db")` breaks test isolation. Use deferred init.
- **Using `yaml.load()` instead of `yaml.safe_load()`:** `yaml.load` can execute arbitrary Python. Always use `safe_load` for file content.
- **Calling `db.create_tables()` at import time:** Tables must be created after `db.init()` is called. Put it in the init function, not at module top level.
- **Storing FSRS Card fields as separate columns prematurely:** The full FSRS state is a JSON blob. Store `card.to_json()` in a `TextField` and cache the `due` datetime as a separate indexed column for query performance.
- **Forgetting `safe=True` in `create_tables()`:** Without it, re-running init will raise an error if tables already exist.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Spaced repetition scheduling | Custom interval math | `fsrs` 6.3.1 | FSRS-6 has 21 tuned parameters; hand-rolled SM-2 will underperform and lack stability/difficulty modeling |
| CLI argument parsing + help | argparse wrappers | Typer 0.24.1 | Type hints auto-generate `--help`, shell completion, error messages |
| SQLite schema management | Raw `CREATE TABLE` strings | Peewee 4.0.1 | `create_tables(safe=True)` handles idempotent schema setup; model layer prevents SQL injection |
| YAML safety | `yaml.load()` + custom safeties | `yaml.safe_load()` | `yaml.load` is equivalent to `pickle.load` in danger; `safe_load` is the one-line fix |
| Terminal formatting | ANSI escape codes | Rich (via Typer) | Rich handles colors, panels, tables across platforms including Windows |
| Config file parsing | Custom TOML parser | `tomllib` (stdlib 3.11+) | Built into Python 3.11+; zero dependency, standard |
| Bundled file access | `__file__`-relative paths | `importlib.resources.files()` | Works in zip-installed packages; `__file__` breaks in some install modes |

**Key insight:** The FSRS algorithm is deceptively complex. FSRS-6 models both long-term forgetting curves and same-day short-term review patterns. Any custom implementation would require months of tuning to approach the library's performance.

---

## Common Pitfalls

### Pitfall 1: Test Pollution via Shared DB State

**What goes wrong:** Tests that use the real `~/.hackmyskills/data.db` pollute each other and corrupt user data.

**Why it happens:** The deferred `db` object is module-level. If tests don't re-initialize it with a temp path, they share state.

**How to avoid:** Use a `conftest.py` fixture that calls `db.init(tmp_path / "test.db")` before each test and `db.close()` after. Use `monkeypatch` to override any config reads of the home directory.

**Warning signs:** Tests pass alone but fail when run together; reviewer data shows up across tests.

### Pitfall 2: Hatchling Skipping YAML Data Files

**What goes wrong:** `pip install -e .` succeeds, but `importlib.resources.files("hms.content")` returns an empty directory — bundled YAML files are missing.

**Why it happens:** Hatchling excludes non-Python files by default when using `src/` layout unless explicitly included.

**How to avoid:** Add to `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/hms"]

# Ensure YAML files inside the package are included:
[tool.hatch.build.targets.wheel.force-include]
"src/hms/content" = "hms/content"
```

Alternatively, include them via glob: `include = ["src/hms/content/*.yaml"]`.

**Warning signs:** `importlib.resources.files("hms.content").iterdir()` yields no items after install.

### Pitfall 3: FSRS `Card.due` is Timezone-Aware

**What goes wrong:** Comparing `card.due` (UTC-aware `datetime`) with a naive `datetime.now()` raises `TypeError`.

**Why it happens:** `fsrs` 6.3.1 returns timezone-aware datetimes. SQLite stores them as strings. Peewee's `DateTimeField` round-trips naive datetimes.

**How to avoid:** Always use `datetime.now(timezone.utc)` for comparisons. When querying due cards, normalize the stored string to UTC-aware on load, or use Peewee's `ISODateTimeField` which preserves UTC offset.

**Warning signs:** `TypeError: can't compare offset-naive and offset-aware datetimes` in scheduler or query code.

### Pitfall 4: FSRS State Lost on Partial Update

**What goes wrong:** Only `due` is updated in the DB after a review but the full FSRS state blob is not; on the next review the card behaves as new.

**Why it happens:** Developer updates the `due` column for query performance but forgets to also update `fsrs_state`.

**How to avoid:** Always update both `due` and `fsrs_state` atomically in a single `save()` call.

### Pitfall 5: `hms` Command Not Available After `pip install -e .`

**What goes wrong:** `pip install -e .` succeeds but `hms` is not on PATH.

**Why it happens:** The virtual environment's `Scripts/` (Windows) or `bin/` directory is not activated.

**How to avoid:** Document that the venv must be activated. The `[project.scripts]` entry point is correct by design — this is a user setup issue, not a packaging bug.

---

## Code Examples

### Full pyproject.toml Skeleton

```toml
# Source: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
[build-system]
requires = ["hatchling >= 1.26"]
build-backend = "hatchling.build"

[project]
name = "hackmyskills"
version = "0.1.0"
description = "Spaced-repetition CLI for DevOps engineers"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.24.1",
    "rich>=13.0",
    "peewee>=4.0.1",
    "fsrs>=6.3.1",
    "pyyaml>=6.0",
]

[project.scripts]
hms = "hms.cli:app"

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/hms"]
```

### Peewee Models for Card and ReviewHistory

```python
# Source: https://docs.peewee-orm.com/en/latest/peewee/database.html
from peewee import (
    SqliteDatabase, Model, CharField, TextField,
    DateTimeField, IntegerField, FloatField, BooleanField
)

db = SqliteDatabase(None)

class BaseModel(Model):
    class Meta:
        database = db

class Card(BaseModel):
    question_id = CharField(unique=True, index=True)  # e.g. "k8s-pod-lifecycle-001"
    question_type = CharField()                        # flashcard | scenario | ...
    topic = CharField(index=True)
    tier = CharField()                                 # L1 | L2 | L3
    tags = TextField(default="")                       # comma-separated or JSON
    version_tag = CharField(default="")
    last_verified = CharField(default="")
    # FSRS state
    fsrs_state = TextField(default="")                 # card.to_json()
    due = DateTimeField(null=True, index=True)         # for "ORDER BY due" queries
    stability = FloatField(default=0.0)
    difficulty = FloatField(default=0.0)
    reps = IntegerField(default=0)
    lapses = IntegerField(default=0)
    state = CharField(default="New")                   # New | Learning | Review | Relearning

class ReviewHistory(BaseModel):
    card = ForeignKeyField(Card, backref="reviews")
    rating = IntegerField()                            # 1=Again 2=Hard 3=Good 4=Easy
    reviewed_at = DateTimeField()
    review_log_json = TextField()                      # review_log.to_json()
```

### First-Run Initialization

```python
from pathlib import Path
from hms.db import db
from hms.models import Card, ReviewHistory

HMS_HOME = Path.home() / ".hackmyskills"

def ensure_initialized() -> None:
    HMS_HOME.mkdir(exist_ok=True)
    (HMS_HOME / "content").mkdir(exist_ok=True)
    db_path = HMS_HOME / "data.db"
    db.init(str(db_path), pragmas={"journal_mode": "wal", "foreign_keys": 1})
    db.create_tables([Card, ReviewHistory], safe=True)
    _copy_bundled_content(HMS_HOME / "content")
```

### pytest conftest.py for Isolation

```python
# Source: https://docs.pytest.org/en/stable/how-to/tmp_path.html
import pytest
from pathlib import Path
from hms.db import db
from hms.models import Card, ReviewHistory

@pytest.fixture(autouse=True)
def isolated_hms_home(tmp_path, monkeypatch):
    hms_home = tmp_path / ".hackmyskills"
    hms_home.mkdir()
    (hms_home / "content").mkdir()
    monkeypatch.setattr("hms.init.HMS_HOME", hms_home)
    db.init(str(hms_home / "test.db"), pragmas={"foreign_keys": 1})
    db.create_tables([Card, ReviewHistory], safe=True)
    yield hms_home
    db.close()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SM-2 interval algorithm | FSRS-6 (21 parameters) | 2024-2025 | Significantly better recall prediction; Anki default since 2023 |
| `setup.py` + `setup.cfg` | `pyproject.toml` + Hatchling | 2021+ (PEP 517/518/621) | Single declarative file; no executable config |
| `pkg_resources` for data files | `importlib.resources.files()` | Python 3.9+ (stable 3.12) | Works in zip installs; `pkg_resources` deprecated |
| `fsrs` v5 (19 params) | `fsrs` v6 (21 params) | fsrs 6.0 release | Better same-day short-term review scheduling |
| Typer `0.9.x` | Typer `0.24.1` | 2025-2026 | API stable; `@app.callback(invoke_without_command=True)` for dashboard default |

**Deprecated/outdated:**
- `setup.py`: Avoid entirely — use `pyproject.toml` with Hatchling
- `yaml.load()`: Unsafe; always use `yaml.safe_load()` per PyYAML deprecation warning
- `pkg_resources.resource_string()`: Deprecated in favor of `importlib.resources`
- `fsrs` parameters for v5 (19 weights): v6 requires 21; migration: append two new defaults

---

## Open Questions

1. **src layout vs flat layout**
   - What we know: Both work with Hatchling; src layout is the modern standard and prevents accidental imports from the project root
   - What's unclear: User's preference (marked as Claude's discretion)
   - Recommendation: Use `src/hms/` layout — it prevents the common "imports work locally but fail after install" bug

2. **FSRS state storage: JSON blob vs individual columns**
   - What we know: `card.to_json()` gives the full FSRS state; `due` is the most-queried field
   - What's unclear: Whether future phases need to query on `stability` or `difficulty` directly
   - Recommendation: Store full state as `fsrs_state` TEXT (JSON blob) + `due` as an indexed `DateTimeField`. Add `stability`, `difficulty`, `reps`, `lapses` as individual columns for Phase 3 adaptive difficulty queries — they're cheap to store and avoid deserializing JSON for stats.

3. **Config file creation on first run**
   - What we know: Config lives at `~/.hackmyskills/config.toml`; `tomllib` is read-only (stdlib)
   - What's unclear: Should a default `config.toml` be written on first run?
   - Recommendation: Yes — write a well-commented default `config.toml` on first run using the bundled template approach (same as YAML content). `tomllib` reads it; writing uses standard `open()`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` section — Wave 0 |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FOUND-01 | `hms --help` exits 0 after install | smoke | `pytest tests/test_cli.py::test_hms_help -x` | Wave 0 |
| FOUND-02 | First run creates `data.db` in temp home | integration | `pytest tests/test_init.py::test_first_run_creates_db -x` | Wave 0 |
| FOUND-03 | YAML files from bundled content loaded without error | unit | `pytest tests/test_loader.py::test_load_bundled_questions -x` | Wave 0 |
| FOUND-04 | YAML with all 4 types passes validation | unit | `pytest tests/test_loader.py::test_all_question_types_valid -x` | Wave 0 |
| FOUND-05 | Question missing base field raises ValueError | unit | `pytest tests/test_loader.py::test_missing_base_field_raises -x` | Wave 0 |
| FOUND-06 | `review_card()` returns updated `due` date | unit | `pytest tests/test_scheduler.py::test_review_updates_due -x` | Wave 0 |
| FOUND-07 | Review rating persisted in ReviewHistory table | integration | `pytest tests/test_models.py::test_review_history_persisted -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/conftest.py` — isolated `hms_home` fixture with tmp_path + monkeypatch + db init/close
- [ ] `tests/test_cli.py` — covers FOUND-01
- [ ] `tests/test_init.py` — covers FOUND-02
- [ ] `tests/test_loader.py` — covers FOUND-03, FOUND-04, FOUND-05
- [ ] `tests/test_scheduler.py` — covers FOUND-06
- [ ] `tests/test_models.py` — covers FOUND-07
- [ ] Framework install: `pip install pytest` (included in `[project.optional-dependencies] dev`)
- [ ] `pyproject.toml` `[tool.pytest.ini_options]` section with `testpaths = ["tests"]`

---

## Sources

### Primary (HIGH confidence)

- [fsrs PyPI page](https://pypi.org/project/fsrs/) — version 6.3.1, release date 2026-03-10, Python >=3.10
- [py-fsrs GitHub](https://github.com/open-spaced-repetition/py-fsrs) — Card fields, Scheduler.review_card() API, to_json/from_json serialization
- [Peewee 4.0.1 SQLite docs](https://docs.peewee-orm.com/en/latest/peewee/sqlite.html) — pragma configuration, deferred init, JSONField, ISODateTimeField
- [Typer PyPI page](https://pypi.org/project/typer/) — version 0.24.1, Python >=3.10
- [Python Packaging User Guide — pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) — Hatchling build-system, scripts entry points
- [Hatch build configuration docs](https://hatch.pypa.io/latest/config/build/) — YAML data file inclusion, packages directive
- [Python 3.12 importlib.resources](https://docs.python.org/3.12/library/importlib.resources.html) — `files()` API for bundled content

### Secondary (MEDIUM confidence)

- [Peewee 4.0.1 database docs](https://docs.peewee-orm.com/en/latest/peewee/database.html) — deferred init pattern verified against official docs
- [pytest tmp_path docs](https://docs.pytest.org/en/stable/how-to/tmp_path.html) — test isolation pattern
- [Typer testing tutorial](https://typer.tiangolo.com/tutorial/testing/) — CliRunner usage

### Tertiary (LOW confidence)

- None — all critical claims verified against official sources.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified on PyPI with current versions and release dates
- Architecture: HIGH — patterns drawn from official Peewee, Typer, and fsrs documentation
- Pitfalls: HIGH — deferred init and timezone pitfalls verified in official Peewee docs; YAML safety from PyYAML official wiki

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable libraries; fsrs is active so check for 6.x patches if implementation is delayed)
