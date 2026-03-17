# Phase 3: Gamification + Adaptive Difficulty - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

XP calculation, daily streak tracking, streak freeze system, level progression, adaptive tier unlocking (L1→L2→L3 per topic), and `hms stats` command. The quiz session display (summary screen, XP line) already exists from Phase 2 with a placeholder formula — this phase replaces that placeholder with real logic and wires up all the gamification state. No interrupt daemon, no AI generation — those are Phase 4 and 5.

</domain>

<decisions>
## Implementation Decisions

### XP Formula
- **Base XP by tier:** L1 = 5 XP, L2 = 10 XP, L3 = 20 XP per card
- **Recall quality multiplier:** Again = 0×, Hard = 0.5×, Good = 1.0×, Easy = 1.5×
  - Again earns zero XP — you didn't know it; Hard earns half; Easy gets a bonus
- **Streak multiplier:** +10% XP per 7-day streak milestone, capped at +50% (applies at day 7, 14, 21, 28, 35+)
  - Applied to the subtotal after tier × rating, rounded to nearest integer
- **Formula:** `xp = round(base_tier_xp * rating_multiplier * streak_multiplier)`
- **Replaces Phase 2 placeholder:** `xp = cards_reviewed * 15` is replaced in `SessionResult.xp`

### Streak & Freeze System
- **Daily streak:** Increments when ≥1 card is reviewed on a calendar day (local date)
- **Missed day:** If no review happened yesterday, streak resets to 0 — unless a freeze is consumed
- **Streak freeze:** Earned every 7 consecutive days; stored as an integer count; consumed automatically on first missed day (not a choice)
- **Freeze display:** Show count in stats as "Freezes: N" — if 0, omit from dashboard to avoid noise
- **Streak check timing:** Evaluated at the start of each `hms quiz` session and on `hms stats`

### Level System
- **10 levels, DevOps-themed names (fixed order):**
  1. Pipeline Rookie
  2. Container Cadet
  3. YAML Wrangler
  4. CI Operator
  5. Cloud Apprentice
  6. Terraform Tinkerer
  7. Cluster Admin
  8. SRE Initiate
  9. Container Captain
  10. DevOps Architect
- **Linear XP progression:** 500 XP per level; 5,000 XP total to reach max
- **Level is derived at display time** from total XP — no separate `level` field needed in DB
- **At max level (DevOps Architect):** Show "Max Level" instead of XP progress bar

### Adaptive Difficulty — Mastery & Unlocking
- **Mastery definition:** A card is mastered when its FSRS `state` field = `"Review"` (promoted out of Learning/Relearning). Stored in `Card.state` (CharField, already in the model).
- **Unlock threshold:** A tier unlocks for a topic when ≥80% of that topic's cards at the current tier are mastered (state = Review)
  - L2 unlocks per-topic: mastered ≥80% of topic's L1 cards
  - L3 unlocks per-topic: mastered ≥80% of topic's L2 cards
- **Mastery % calculation:** `mastered_count / total_count` where total = all cards for that topic+tier in DB
- **Unlock notification:** If a tier just unlocked for any topic during the session, show a highlighted line at the end of the session summary panel:
  - `🔓 L2 kubernetes unlocked! Harder cards are now available.`
  - Check for new unlocks by comparing unlock status before vs. after session
- **Card selection in hms quiz (no --topic):** Serve due cards from all unlocked tiers for all topics. Do not serve L2 cards for a topic if L2 is still locked. Within the due queue, no special tier ordering — FSRS `due` ASC governs.

### hms stats Display
- **Structure:** Single Rich Panel titled "HackMySkills Stats"
- **Top section (summary):**
  - Streak: `🔥 5 days` (or `5 day streak` if emoji unreliable) + Freezes: N (omit if 0)
  - Level name + number: `Level 3 · YAML Wrangler`
  - XP progress bar: `XP: 1240 / 1500  [████████░░] 83%` — use Rich Progress or a manual bar
  - Cards due today: `18 cards due`
- **Per-topic table (bottom of panel):** Rich Table with columns: `Topic | Due | Mastery% | Tier`
  - Mastery% = (state=Review cards) / (total cards for topic) as integer percent
  - Tier = highest tier currently unlocked for that topic (L1/L2/L3)
  - Sort: by Due DESC (most urgent first)
- **No-args dashboard update:** `hms` with no args (dashboard) should now show:
  - Streak + level name (motivating one-liner)
  - Cards due today
  - "Run hms quiz to start" prompt
  - Replaces the Phase 1 placeholder dashboard

### Claude's Discretion
- Exact XP bar character style (block chars vs. Rich's built-in bar)
- Whether to show a level-up message mid-session or only in summary
- How to handle edge case: topic has 0 cards in a tier (treat as unlocked? skip tier?)
- Error display if DB has no review history yet (first-run stats)

</decisions>

<specifics>
## Specific Ideas

- The dashboard (`hms` no args) should feel like checking your Duolingo streak — motivating, not just a help menu. "5 day streak 🔥 · YAML Wrangler · 18 cards due" as the headline.
- The unlock notification in session summary should feel like a moment: the lock emoji opening signals real progress.
- At max level (DevOps Architect), show something satisfying — not just "Max Level" but maybe "Max Level — you've hacked the skills." Tone matches the repo name.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Gamification requirements
- `.planning/REQUIREMENTS.md` §Gamification (GAME-01 through GAME-05) — XP formula spec, streak rules, freeze mechanic, level system, stats command
- `.planning/REQUIREMENTS.md` §Adaptive Difficulty (ADAPT-01 through ADAPT-04) — tier definitions, unlock thresholds, tier-aware card serving

### Existing implementation (what to build on)
- `src/hms/models.py` — `Card.state` (CharField, stores FSRS state), `Card.tier`, `Card.topic`; `ReviewHistory` — use for session stats
- `src/hms/quiz.py` — `SessionResult.xp` (placeholder to replace), `compute_streak()` (exists, verify behavior), session summary rendering
- `src/hms/cli.py` — `_show_dashboard()` to update with streak/level/due

### FSRS state values
- `src/hms/scheduler.py` — `review_card()` returns updated Card; FSRS states: "New", "Learning", "Review", "Relearning" — mastery = "Review"

No external specs beyond REQUIREMENTS.md — all gamification decisions are captured above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SessionResult` dataclass (`quiz.py`) — tracks `total`, `correct`, `topic_stats`, `ratings`; has `.xp` property to replace
- `Card.state` (CharField) — already stores FSRS state strings; query `WHERE state = 'Review'` for mastery counts
- `Card.tier`, `Card.topic` — indexed fields; mastery queries are `SELECT COUNT(*) WHERE topic=X AND tier=Y AND state='Review'`
- `ReviewHistory` — one row per review; `reviewed_at` (naive UTC datetime) — use for streak calculation
- Rich `Panel`, `Table`, `Progress`/manual bar — already installed; `console = Console()` in both cli.py and quiz.py
- `compute_streak()` in quiz.py — exists; verify it handles freeze consumption or add freeze logic here

### Established Patterns
- Rich Panel border_style colors: blue=info, red=error, green=success — keep consistent
- No animations or `time.sleep` — static Rich output only (deferred from Phase 2)
- `ensure_initialized()` called at start of any DB-touching command
- Module-level `console = Console()` — import from quiz.py or create per-module (quiz.py uses its own to avoid circular imports)

### Integration Points
- `SessionResult.xp` — replace placeholder with tier+rating+streak formula
- `_show_dashboard()` in cli.py — update to query streak, level, due count
- `run_session()` in quiz.py — add unlock check after session, inject unlock notifications into summary
- New `hms stats` command: `@app.command()` in cli.py — queries Card and ReviewHistory tables

</code_context>

<deferred>
## Deferred Ideas

- XP animation / level-up fanfare — Rich doesn't animate well in static mode (deferred from Phase 2)
- Badges/achievements (GAME-V2-01) — v2 requirement, not Phase 3
- Weekly/monthly summary report (GAME-V2-02) — v2 requirement
- FSRS optimizer to personalize weights (GAME-V2-03) — v2 requirement

</deferred>

---

*Phase: 03-gamification-adaptive-difficulty*
*Context gathered: 2026-03-15*
