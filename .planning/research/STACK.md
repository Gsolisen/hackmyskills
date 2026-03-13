# Technology Stack

**Project:** HackMySkills — CLI-based DevOps Skill Trainer
**Researched:** 2026-03-13
**Mode:** Ecosystem Research

---

## Recommended Stack

### Language: Python 3.12

Use Python 3.12 (not 3.13+, not Node.js). Rationale:

- **Windows-first requirement favors Python.** The notification ecosystem (`desktop-notifier` via WinRT), scheduling (`APScheduler`), and terminal UI (`Rich`) are better maintained on Python for Windows than their Node equivalents.
- **3.12 specifically** because `typer` requires `>=3.10`, `pydantic-settings` requires `>=3.10`, and 3.12 is the stable LTS-adjacent release with full library support. 3.13 is too new — several libraries have lagged wheel availability on Windows for new CPython minor versions.
- **Not Node.js**: Node's `blessed`/`ink` terminal ecosystem is thinner on Windows, `node-notifier` has persistent Windows WinRT issues, and there is no mature spaced repetition library in the Node ecosystem. Python wins on all three key dimensions here.

---

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.12.x | Runtime | LTS-adjacent, full library support, Windows-first strength |
| Typer | 0.24.1 | CLI framework | Type-hint-driven, zero-boilerplate commands, integrates directly with Rich for formatted output. Better than Click for greenfield: less ceremony, auto-generated help. Built on Click so escape hatches exist. |
| Rich | 14.3.3 | Terminal output | Tables, progress bars, panels, markdown rendering, colored text. The standard for Python CLI UX in 2025. Works natively on Windows 11. |
| questionary | 2.1.1 | Interactive prompts | Multi-choice, text-input, confirmation prompts during quiz sessions. Built on prompt-toolkit. Better API than raw prompt-toolkit for this use case. |

### Spaced Repetition

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| fsrs | 6.3.1 | Scheduling algorithm | FSRS (Free Spaced Repetition Scheduler) is the current state-of-the-art. Trained on 700M real reviews from 20K users. Adopted by Anki in 2023. Delivers 20-30% fewer reviews vs SM-2 for equivalent retention. Has Python `Card`, `Rating`, and `Scheduler` objects that serialize to JSON — slots cleanly into Peewee storage. |

Do NOT use `supermemo2` (SM-2). It is accurate but architecturally dated — FSRS supersedes it for new implementations. Do NOT implement a custom algorithm from scratch; FSRS covers the problem correctly.

### Persistence

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Peewee | 4.0.1 | ORM + SQLite | Lightweight (~6,600 LOC), no separate server, ships with SQLite support via Python's stdlib `sqlite3`. The right size for a local CLI tool — SQLAlchemy is overkill, raw SQL is under-abstracted. Peewee 4.0 released Feb 2026 and is Production/Stable. |

Database file lives in `~/.hackmyskills/data.db` (user home directory). This keeps the tool portable and avoids permission issues on Windows.

Do NOT use SQLAlchemy — it is enterprise-sized for this problem. Do NOT use a flat JSON file — it cannot handle efficient queries across review history for 500+ cards.

### AI Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| anthropic | 0.84.0 | Claude API client | Official Python SDK. Supports Python 3.9-3.14. Used for AI question generation on demand. The SDK exposes `anthropic.Anthropic()` with synchronous `client.messages.create()` — no async required for a CLI tool that calls AI infrequently. |

Integration pattern: a single `ai_generator.py` module wraps the SDK. The Claude API key is read from environment variable `ANTHROPIC_API_KEY` (standard convention). Use `claude-3-5-haiku-20241022` as the default model for question generation — fast and cheap, sufficient for structured JSON question output.

Do NOT use LangChain — it adds dependency weight and abstraction for what is a single, simple API call pattern.

### Notifications (Interrupt Mode)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| desktop-notifier | 6.2.0 | System notifications | Cross-platform (Windows via WinRT, macOS via Notification Center, Linux via dbus). Production/Stable. This is the right library: `notify-py` works but is less actively maintained; `win11toast` is Windows-only and breaks the cross-platform requirement. |

The interrupt-mode flow: `desktop-notifier` fires a "Time to practice!" toast notification. Clicking it (or running `hms quiz`) launches the CLI session. Desktop-notifier's async API should be wrapped with `asyncio.run()` since the rest of the app is synchronous.

Windows caveat: WinRT-based notifications require the app to be run at least once with a registered App User Model ID (AUMID) on some Windows 11 builds. `desktop-notifier` handles this internally, but the first notification may prompt a permissions dialog.

### Scheduling (Interrupt Triggers)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| APScheduler | 3.11.2 | Background scheduling | The `BackgroundScheduler` runs in a daemon thread, fires notifications at intervals (e.g., every 90 minutes during working hours). Stores job state to SQLite via the same Peewee DB. |

**Architecture decision — daemon vs Windows Task Scheduler:**

Use a persistent daemon process (`hms daemon`) rather than Windows Task Scheduler. Rationale: Task Scheduler on Windows is reliable but requires admin setup, has WinRT notification interaction quirks, and cannot easily be started/stopped/configured from Python. A Python daemon started on login (via Windows Startup folder) is simpler, self-contained, and cross-platform. APScheduler `BackgroundScheduler` is the right primitive for this.

The daemon process must be lightweight: only APScheduler + desktop-notifier in memory. Quiz logic loads on notification click.

### Configuration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pydantic-settings | 2.13.1 | Config management | Reads from `~/.hackmyskills/config.toml` + environment variables, with type validation and sensible defaults. Pydantic v2 backend means fast validation. Requires Python >=3.10, consistent with the rest of the stack. |

Config lives at `~/.hackmyskills/config.toml`. User edits it directly (plain TOML) to change notification frequency, working hours, enabled skill tracks, etc.

### Content / Question Bank

| Format | Purpose | Why |
|--------|---------|-----|
| YAML files | Question bank storage | Human-editable without touching Python code. Questions organized by skill track (`k8s.yaml`, `terraform.yaml`, etc.). YAML is friendlier than JSON for multi-line text (command scenarios, long explanations). Python stdlib `yaml` via PyYAML covers this. |

| Technology | Version | Purpose |
|------------|---------|---------|
| PyYAML | 6.0.2 | YAML parsing for question files |

---

### Development Tooling

| Tool | Version | Purpose | Why |
|------|---------|---------|-----|
| uv | latest | Package + project manager | Rust-powered, 10-100x faster than pip. `uv init`, `uv add`, `uv sync` cover the full workflow. Replaces pip + virtualenv + pip-tools. Standard recommendation for new Python projects in 2025. |
| Ruff | latest | Linter + formatter | Replaces Black + Flake8 + isort in one tool. Fast, opinionated, zero-config. |
| pytest | 8.x | Testing | Standard. Works with Typer's test runner. |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| CLI framework | Typer | Click | Click requires more boilerplate; Typer is built on Click so migration is possible, but for greenfield Typer wins |
| CLI framework | Typer | argparse | argparse has no Rich integration, no type hints ergonomics |
| Algorithm | FSRS (fsrs 6.3.1) | SM-2 (supermemo2) | SM-2 is a 1987 algorithm; FSRS is trained on real data and outperforms by 20-30% efficiency |
| ORM | Peewee | SQLAlchemy | SQLAlchemy is enterprise-sized; too much abstraction and startup overhead for a CLI tool |
| ORM | Peewee | raw sqlite3 | Raw sqlite3 requires manual schema management and migration handling |
| Notifications | desktop-notifier | win11toast | win11toast is Windows-only; breaks cross-platform requirement |
| Notifications | desktop-notifier | plyer | plyer is less actively maintained and has more limited Windows 11 support |
| AI | anthropic SDK directly | LangChain | LangChain adds 50+ transitive dependencies for what is one API call pattern |
| Language | Python | Node.js | Node's Windows notification and spaced repetition ecosystem is weaker; Python wins on all three key dimensions |
| Scheduling | APScheduler daemon | Windows Task Scheduler | Task Scheduler requires admin setup, can't be started/stopped from Python, has WinRT notification interaction quirks |
| Config | pydantic-settings + TOML | .env only | TOML is more readable for user-facing config with sections, comments, and non-secret values |

---

## Installation

```bash
# Project setup (uv)
uv init hackmyskills
cd hackmyskills
uv python pin 3.12

# Core runtime dependencies
uv add typer rich questionary fsrs peewee pydantic-settings anthropic desktop-notifier apscheduler pyyaml

# Dev dependencies
uv add --dev pytest ruff pyinstaller
```

## Packaging for Distribution

Primary distribution path: `pipx install hackmyskills` after publishing to PyPI. This gives Windows users a clean isolated install with the `hms` command on PATH.

Secondary path: PyInstaller `--onefile` for a standalone `.exe` that does not require Python to be installed. Use this for distributing to colleagues who don't have Python.

```bash
# Standalone Windows exe
uv run pyinstaller --onefile --name hms src/hackmyskills/__main__.py
```

---

## Platform Notes: Windows 11

- **Rich**: Works natively on Windows 11 with Windows Terminal or PowerShell 7+. Older `cmd.exe` has limited color support — acceptable tradeoff for a DevOps audience.
- **desktop-notifier**: Uses WinRT bridge on Windows 11. Requires the package be invoked at least once to register notification permissions. First run may show a system permissions prompt.
- **APScheduler daemon**: Runs as a background Python process. Add a shortcut to the Windows Startup folder (`shell:startup`) to auto-start on login.
- **SQLite / Peewee**: No Windows-specific issues. SQLite is bundled with CPython and works identically cross-platform.
- **fsrs**: Pure Python, no native extensions. Works on all platforms without compilation.
- **Path conventions**: All file paths use `pathlib.Path.home() / ".hackmyskills"` — never hardcoded Windows paths. This ensures cross-platform portability.

---

## Sources

- Typer: https://typer.tiangolo.com/ | https://pypi.org/project/typer/ (v0.24.1, Feb 2026)
- Rich: https://pypi.org/project/rich/ (v14.3.3, Feb 2026)
- questionary: https://pypi.org/project/questionary/ (v2.1.1, Aug 2025)
- fsrs: https://pypi.org/project/fsrs/ (v6.3.1, Mar 2026)
- FSRS vs SM-2: https://memoforge.app/blog/fsrs-vs-sm2-anki-algorithm-guide-2025/ | https://github.com/open-spaced-repetition/fsrs4anki/wiki
- anthropic SDK: https://pypi.org/project/anthropic/ (v0.84.0, Feb 2026)
- Peewee: https://pypi.org/project/peewee/ (v4.0.1, Mar 2026)
- desktop-notifier: https://pypi.org/project/desktop-notifier/ (v6.2.0, Aug 2025)
- APScheduler: https://pypi.org/project/APScheduler/ (v3.11.2, Dec 2025)
- pydantic-settings: https://pypi.org/project/pydantic-settings/ (v2.13.1, Feb 2026)
- uv: https://docs.astral.sh/uv/
