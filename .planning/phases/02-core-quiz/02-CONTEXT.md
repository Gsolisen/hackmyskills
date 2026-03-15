# Phase 2: Core Quiz - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Terminal quiz session delivering all four question types (flashcard, command-fill, scenario, explain-concept). Session serves due cards first then new cards, up to a daily cap. Each card type has a defined input/rating flow. Session ends with a summary screen. No gamification math in this phase — XP is *displayed* but the calculation formula comes from Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Question Display & Layout
- **Screen handling:** Clear the terminal on each new card — every question gets a clean slate, like a flashcard app. No scroll history during the session.
- **Progress indicator:** Progress bar + card count shown at the top of every card screen. Format: `Card 4/10 ──────────── 40%`. Use Rich Progress or a manual Rich Rule + text line.
- **Card metadata:** Subtle single-line header above the question in dim text: `[kubernetes · L2]`. Visible but not distracting — topic and difficulty tier always present.
- **Flashcard layout:** Question shown in a Rich Panel (blue/cyan border). After reveal, answer shown in a second Rich Panel (green border). Two distinct panels, sequential display — not side-by-side.
- **Command-fill layout:** Prompt text in a Panel, then an input line. After submission, show result (correct ✓ in green / incorrect ✗ in red) plus the canonical answer if wrong.
- **Scenario layout:** Situation text in a Panel, then A/B/C/D options listed below. Single keypress selects. After selection, show correct answer + explanation.
- **Explain-concept layout:** Prompt in a Panel, multiline text input (standard terminal input), then model answer shown in a Panel for self-rating.

### Rating & Input UX
- **Flashcard reveal:** Any keypress (space or enter) flips the card to show the answer. Simple, fast, no thinking required.
- **Self-rating keys:** Number keys **1–4** after reveal:
  - `1` = Again (red)
  - `2` = Hard (orange)
  - `3` = Good (green)
  - `4` = Easy (blue)
  - Labels shown on screen so user doesn't need to memorize.
- **Command fill-in correctness:** **Exact match, case-insensitive** — no fuzzy tolerance. User must type the command correctly (modulo case). This keeps FSRS signal clean; a typo is a real miss.
- **Scenario answer:** **Multiple choice A/B/C/D** — single keypress, no enter needed. After selection, immediately show whether correct + brief explanation text.
- **Explain-concept:** User types a free-text explanation (standard `input()` line), then model answer is shown in a green Panel. Self-rating via 1–4 keys, same as flashcard.

### Session Flow & Quit Behavior
- **Quit anytime:** Pressing `q` or `Ctrl-C` ends the session cleanly. Cards already reviewed are committed to the DB. A condensed mini-summary is shown for completed cards, then return to shell.
- **Streak credit:** Any review counts — if at least 1 card was reviewed today, the daily streak is maintained. Encourages showing up even for a 2-minute session.
- **Skip:** No skip option. If a card is unknown, rate it `1` (Again) — this is the correct FSRS signal. Skip would corrupt due dates.
- **Natural end:** When daily cap is reached (or card queue exhausted), show the full summary screen. User presses any key to return to shell prompt.
- **Daily cap:** Default 25 cards. Configurable in `~/.hackmyskills/config.toml` under `[quiz] daily_cap = 25`.
- **Card order:** Due cards (sorted by `due` ASC) served first. When due queue exhausted, new cards (`due IS NULL`, ordered by topic then ID) fill up to the cap.
- **Topic filter:** `hms quiz --topic kubernetes` restricts card selection to `WHERE card.topic = 'kubernetes'`. Same ordering rules apply within the filtered set.

### Session Summary Screen
- **Format:** Full Rich Panel — feels like completing a Duolingo lesson. Shown after every session (natural end or early quit with ≥1 card reviewed).
- **Contents:**
  - Cards reviewed (e.g., `10 cards`)
  - Accuracy % (correct or self-rated Good/Easy out of total — Again/Hard = incorrect for accuracy calc)
  - XP earned — bold yellow `+150 XP` (no animation, just emphasis)
  - Current streak — `🔥 5 days` (or plain `5 day streak` if emoji is platform-risky)
  - Next session: `8 cards due tomorrow`
- **Per-topic breakdown:** Only shown if the session included more than one topic — a small Rich table showing `Topic | Cards | Accuracy` rows. Single-topic sessions skip the table to avoid noise.
- **XP display:** Bold highlighted number only — no typewriter animation, no time.sleep tricks. Rich doesn't animate well in static output; skip the gimmick.
- **XP formula placeholder:** Phase 2 displays XP but Phase 3 owns the formula. For Phase 2, use a simple placeholder: `xp = cards_reviewed * 15` (will be replaced in Phase 3 by the real tier-weighted formula).

### Error & Edge Cases
- **Empty queue:** If no cards are due and no new cards exist for the given topic, show a message: "Nothing to review right now — come back tomorrow!" Return to shell without a summary panel.
- **No cards for topic:** If `--topic kubernetes` finds no cards at all, show a Rich error box (red panel): "No cards found for topic 'kubernetes'. Run `hms topics` to see available topics."
- **Single-question session (quit after 1 card):** Still show mini-summary. Don't suppress the summary just because it was short.

</decisions>

<specifics>
## Specific Ideas

- The progress bar line (`Card 4/10 ──────────── 40%`) should use Rich's built-in `Progress` or a simple `Rule` with a fraction — keep it lightweight, not a full multi-line progress widget.
- The `1=Again 2=Hard 3=Good 4=Easy` labels should always be visible on screen after the answer is revealed — don't make the user guess the key mapping.
- The "any keypress to flip" mechanic for flashcards should use `readchar` or `msvcrt.getwch()` on Windows for a true single-keypress feel — no enter required. Same for the 1–4 rating and A–D scenario selection.
- For the accuracy calculation: Again (1) and Hard (2) count as "incorrect"; Good (3) and Easy (4) count as "correct". Self-rated correctly even if the user lied — FSRS governs the real scheduling anyway.
- The "quit mini-summary" (when pressing q mid-session) should be shorter than the full summary — just 2–3 lines: cards reviewed, XP earned, streak status. No per-topic table.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets (from Phase 1)
- `src/hms/cli.py` — Typer app, `console = Console()`, Rich Panel pattern for dashboard
- `src/hms/models.py` — `Card` model with `due`, `topic`, `tier`, `question_type`, `fsrs_state` fields; `ReviewHistory` for persisting ratings
- `src/hms/scheduler.py` — `review_card(card, rating) -> (Card, ReviewLog)` — call this after each card rating
- `src/hms/db.py` — `db` deferred init; `initialize_db()` pattern
- `src/hms/init.py` — `ensure_initialized()` — call at start of `hms quiz` to guarantee DB is ready
- `src/hms/loader.py` — `load_questions()` — returns list of validated question dicts from YAML files
- Rich `Console`, `Panel`, `Rule` already installed and used in cli.py

### Established Patterns
- `ensure_initialized()` called at start of any command that touches the DB
- Rich `Panel` with border_style color for semantic meaning (blue=info, red=error established in Phase 1)
- `console = Console()` at module level in cli.py — import and reuse in quiz module
- Typer subcommand pattern: `@app.command()` decorator in cli.py

### Integration Points
- `Card.due` (DateTimeField, naive UTC) — query `WHERE due <= now()` for due cards, `IS NULL` for new cards
- `Card.topic` — filter by `--topic` flag
- `ReviewHistory` — create one row per card rating during session
- `scheduler.review_card(card_model, fsrs.Rating)` — call after rating; update Card fields with returned state
- `config.toml [quiz] daily_cap` — read via `hms.config` at session start

### Key Dependency
- Single-keypress input requires `readchar` library (cross-platform) or Windows-specific `msvcrt` — Phase 1 did not install this. Must be added to `pyproject.toml` dependencies.

</code_context>

<deferred>
## Deferred Ideas

- XP animation / typewriter effect — deferred; Rich doesn't animate well in static mode
- "Continue past daily cap" option at summary — deferred to Phase 3 or config option
- Session replay / review past answers — different phase
- Sound effects on correct answer — out of scope for CLI

</deferred>

---

*Phase: 02-core-quiz*
*Context gathered: 2026-03-15*
