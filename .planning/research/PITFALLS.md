# Domain Pitfalls

**Domain:** CLI-based gamified spaced repetition skill trainer (DevOps)
**Researched:** 2026-03-13

---

## Critical Pitfalls

Mistakes that cause rewrites, user abandonment, or a fundamentally hollow product.

---

### Pitfall 1: Review Debt — The Queue That Kills Habits

**What goes wrong:** The SRS algorithm schedules cards without a daily cap. A user misses two days, returns to find 200+ reviews due, feels dread instead of satisfaction, and never opens the tool again. SRS debt is the single most cited reason people quit spaced repetition tools permanently. The problem compounds: a missed day creates more due cards, which creates more dread, which creates more skipped days.

**Why it happens:** Developers ship the pure algorithm (review everything due) without rate-limiting the daily output. Missing days is inevitable; the system must handle it gracefully, not punish it.

**Consequences:** Tool abandonment is abrupt and permanent. Unlike a missed gym session, a 200-card backlog is visible and quantified, making the failure feel concrete.

**Warning signs:**
- Daily due-card count grows unbounded after even a single missed day
- No cap on `new cards per day` or `reviews per day` in session config
- No "catch up" or "vacation mode" concept in the scheduler

**Prevention:**
- Hard cap daily reviews (e.g., 50 reviews max per day regardless of debt)
- When debt accumulates, deprioritize already-forgotten cards (stale) over recently-due cards (fresh)
- Add a "streak shield" mechanic (one grace day per week that doesn't break the streak) — Duolingo's "Weekend Amulet" data shows this increases long-term retention, not laziness
- Show "You're caught up" as a positive terminal state, never show a raw backlog number

**Phase to address:** Phase 1 (SRS core) — the cap and debt policy must be built into the scheduler from the start, not retrofitted.

---

### Pitfall 2: Cold Start Failure — Alienating New Users Before They're Hooked

**What goes wrong:** A new user with no history gets questions calibrated for a median learner. They either get trivial questions ("What does CI stand for?") that feel insulting to a working DevOps engineer, or hard questions that punish them before the tool has learned anything. Either way, the first session fails to demonstrate value.

**Why it happens:** SM-2 and FSRS assign identical starting difficulty to all cards (EF=2.5 in SM-2). Without an initial placement quiz or user-declared skill level, the system has no signal.

**Consequences:** First session is a poor demonstration of the tool's core value proposition. Drop-off at session 1-3 is the highest-risk window for any habit tool.

**Warning signs:**
- No onboarding flow or skill-level declaration
- All cards start at identical default difficulty
- First session indistinguishable from a random quiz

**Prevention:**
- Run a 5-10 question placement quiz at first launch to calibrate starting difficulty per topic
- Allow users to declare track experience explicitly ("I use Kubernetes daily" vs "Never touched it")
- Use question performance from the placement quiz to seed initial interval values rather than defaults
- Make the first full session feel "smart" — it should surface things the user almost-but-not-quite knows

**Phase to address:** Phase 1 (core engine) for algorithm seeding; Phase 2 (onboarding UX) for the placement quiz.

---

### Pitfall 3: Gamification That Rewards Activity, Not Learning

**What goes wrong:** XP, streaks, and badges are awarded for completing sessions regardless of whether actual learning occurred. Users optimize for the reward, not the skill. They rush answers, click through without thinking, or choose easy cards. The gamification becomes a score to game rather than a signal of growth.

**Why it happens:** The easiest implementation awards XP per card answered, per session completed, per streak day. This is output-based, not outcome-based. Research confirms the overjustification effect: when extrinsic rewards are prominent enough, they replace intrinsic motivation. Users who initially enjoyed learning start resenting the obligation.

**Consequences:** The tool feels hollow after 2-4 weeks. Users describe the experience as "going through the motions." Streaks become a source of anxiety rather than satisfaction. Some users quit immediately after breaking a long streak.

**Warning signs:**
- XP formula is `sessions_completed * constant` rather than tied to correct recalls
- Streak is binary (maintained or broken) with no grace/shield mechanic
- No distinction between "answered quickly and confidently" vs "guessed and got lucky"

**Prevention:**
- Award XP based on quality of recall: correct on first attempt and fast = more XP than slow and struggled
- Tie XP to performance on hard/weak cards, not easy ones (don't reward reviewing cards you already know well)
- Make streaks flexible — a streak measures weekly consistency, not daily perfection
- Add a "mastery" indicator per topic that is slow to move and hard to fake; this is the real progress signal
- Never use guilt-driven copy ("You've been away for 3 days. The owl is disappointed.")

**Phase to address:** Phase 2 (gamification layer) — design the XP formula before shipping any rewards UI.

---

### Pitfall 4: AI-Generated Questions With Factual Errors or Misleading Distractors

**What goes wrong:** Claude generates a Kubernetes question where one of the "wrong" answers is actually correct in a specific version, or a Terraform question where the syntax has changed since training data cutoff, or a distractor option that is technically ambiguous. The user learns the wrong answer, or worse, disputes a correct answer and loses trust in the tool entirely.

**Why it happens:** LLMs confidently produce plausible-sounding but incorrect technical details. DevOps tooling changes rapidly (Kubernetes deprecates APIs regularly; Terraform syntax evolves across provider versions; cloud service names change). AI-generated content has no temporal awareness by default.

**Consequences:** Actively harmful learning (user internalizes wrong information). Trust collapse is fast and hard to recover — a single provably wrong question undermines confidence in all questions.

**Warning signs:**
- AI questions go directly into the question bank without human review
- Question generation prompt does not specify tool versions
- No mechanism for users to flag questions as incorrect
- Distractor options generated without a "none of the distractors should be technically arguable" constraint

**Prevention:**
- Every AI-generated question must be tagged with a `generated_at` date and the tool version context used in the prompt
- Include version constraints in generation prompts: "Assume Kubernetes 1.29+, Terraform 1.5+, AWS CLI v2"
- Never display an AI-generated question without at least a soft validation step — either human review flag or a confidence threshold
- Build a question flagging system from day one (user can mark "this seems wrong") — this becomes the quality feedback loop
- Cache generated questions in the local question bank; regenerating on every session creates both cost and consistency issues
- Maintain a curated "golden set" of hand-verified questions for high-stakes topics (Kubernetes RBAC, Terraform state, IAM policies)

**Phase to address:** Phase 1 (question bank design) for the flagging schema; Phase 3 (AI generation) for generation prompts and the caching layer.

---

### Pitfall 5: Interrupt Mode That Trains Users to Dismiss It

**What goes wrong:** System notifications pop up too frequently, at inopportune times (during a deep work session, during a meeting, during a build), or are too long to act on in 30 seconds. Within a week, the user adds the notifier to the "dismiss immediately" reflex. The interrupt habit never forms because the signal became noise.

**Why it happens:** Developers set a default interrupt frequency that feels "active" from their perspective (every 90 minutes) without considering that knowledge workers have irregular focus cycles. The notification itself requires too much context to engage with — it's not actionable in 15-30 seconds.

**Consequences:** Interrupt mode is the entire habit-formation mechanism. If it fails, the user only uses the tool when they remember to — which is rare, and the habit never forms. After an interruption it takes ~23 minutes to regain deep focus; a poorly-timed interrupt carries real cognitive cost.

**Warning signs:**
- Fixed interval timer with no user-configurable schedule
- Notification click opens full CLI session rather than a single quick question
- No quiet hours / do-not-disturb integration
- Notification content is a generic "Time to study!" rather than the first question itself

**Prevention:**
- Default interrupt interval should be long (every 3-4 hours), not short — users will increase frequency if they want more
- Make notification content the question itself (or first 1-2 words of the question): "Quick: What does `kubectl rollout undo` do?" — the user can answer mentally before even opening the terminal
- Support quiet hours configuration from day one (no notifications 9am-11am, no notifications after 6pm, etc.)
- Keep the interrupt session to exactly 1-3 questions; do not allow it to expand into a full review session
- On Windows, use `plyer` or `desktop-notifier` — test on Windows 11 specifically; Windows notification APIs differ from macOS/Linux

**Phase to address:** Phase 2 (interrupt mode) — quiet hours and single-question format must be designed before the scheduler is built, not after.

---

## Moderate Pitfalls

---

### Pitfall 6: Question Type Monotony Kills Engagement

**What goes wrong:** Every session is multiple-choice. Even if the content is excellent, the format becomes predictable and mechanical after two weeks. The user stops thinking and starts pattern-matching ("the longest answer is usually right").

**Prevention:**
- Mix question types in every session: multiple choice, command fill-in (partial command completion), explain-the-concept (short free-text with keyword matching), scenario ("Given this Terraform error output, what's wrong?")
- Weight question type by topic: bash/kubectl benefit from command fill-in; concepts benefit from explain-the-concept
- Reserve scenario questions for "mastered" topics — they require more time and should reward demonstrated knowledge

**Phase to address:** Phase 1 (question schema must support type field); Phase 2 (type rotation in session engine).

---

### Pitfall 7: Difficulty That Doesn't Adapt — The Plateau Problem

**What goes wrong:** The SRS algorithm surfaces weak cards more often (correct), but the difficulty of the questions themselves never increases. A user who truly masters "What is a Pod?" keeps getting "What is a Pod?" forever, just at increasing intervals. No progression in question depth.

**Prevention:**
- Tag questions with difficulty tiers (L1: definition, L2: application, L3: troubleshooting/edge case)
- When a topic's cards are consistently recalled correctly at L1, introduce L2 cards for that topic
- The SRS scheduler manages when to show each card; a separate difficulty-progression layer decides which tier of cards to unlock

**Phase to address:** Phase 1 (card schema needs difficulty tier field); the progression logic can be Phase 2 or 3.

---

### Pitfall 8: Claude API Cost Spiral on Heavy Use

**What goes wrong:** AI question generation is called on demand per session. A power user running 5 sessions per day with 20 questions each generates 100 API calls with no caching. Costs accumulate faster than expected; the app becomes expensive to run on personal API keys.

**Prevention:**
- Generate questions in batches (e.g., generate 50 questions at a time, cache them locally)
- Use prompt caching for the system prompt and topic context (same prefix reused across calls — Claude API prompt caching can effectively increase ITPM capacity 5x at no extra cost)
- Set a hard daily generation limit (e.g., max 20 new AI questions per day; use cached questions otherwise)
- Track generated question count and cost in a local stats file so the user has visibility

**Phase to address:** Phase 3 (AI integration) — the caching and batching architecture must be designed before the first generation call.

---

### Pitfall 9: SM-2 "Ease Hell" — Cards Stuck at Minimum Difficulty

**What goes wrong:** SM-2's ease factor decays each time a card is marked "Hard" or "Again". Cards that are genuinely difficult accumulate very low ease factors and are reviewed every 1-2 days forever, consuming a disproportionate fraction of each session. The user never escapes these cards and the backlog grows.

**Prevention:**
- Use FSRS instead of SM-2 — FSRS self-corrects, is 20-30% more review-efficient, and does not have the ease death spiral
- If SM-2 is used, set a minimum ease floor (e.g., never below 1.8) and implement an "ease reset" mechanism after N consecutive correct recalls
- Monitor the distribution of card ease factors in session stats; a bimodal distribution (many cards near minimum ease) is a warning sign

**Phase to address:** Phase 1 (algorithm selection) — choose FSRS over SM-2 at the start; retrofitting is expensive.

---

## Minor Pitfalls

---

### Pitfall 10: Progress Visualization That Shows Effort, Not Growth

**What goes wrong:** The stats screen shows "total cards reviewed: 847" and "current streak: 23 days." These numbers feel good but don't demonstrate actual skill growth. The user cannot see whether they're actually getting faster or more accurate on topics they once struggled with.

**Prevention:**
- Track per-topic accuracy trend over time (rolling 7-day vs 30-day accuracy per topic)
- Show "Topics you've mastered" and "Topics still weak" as the primary progress summary
- Track average response time per question type — speed improvement is a real signal that knowledge is internalizing
- Defer raw "total reviewed" stats to a secondary detail view; they reward volume, not quality

**Phase to address:** Phase 2 (progress tracking UI).

---

### Pitfall 11: Question Bank Staleness for Fast-Moving DevOps Tools

**What goes wrong:** A curated question bank written at project launch becomes partially wrong within 6-12 months. Kubernetes deprecates APIs, Terraform introduces new syntax, AWS renames services. Users notice outdated answers and lose trust.

**Prevention:**
- Tag every question with a `last_verified` date and the relevant tool version
- Surface version-tagged warnings in question display: "This question assumes Kubernetes 1.29"
- Design the question file format so that outdated questions can be easily filtered or retired
- Treat the AI generation layer as a freshness mechanism — generate new questions on a topic when its curated questions age past a threshold

**Phase to address:** Phase 1 (question schema) for metadata fields; Phase 3 for freshness-driven AI generation.

---

### Pitfall 12: Windows Notification Reliability Issues

**What goes wrong:** The chosen notification library (`plyer`, `desktop-notifier`, `win10toast`) works in development but silently fails in certain Windows 11 configurations — Focus Assist mode, battery saver, group policy restrictions, or missing COM dependencies. The interrupt habit mechanism breaks invisibly.

**Prevention:**
- Test notification delivery on Windows 11 with Focus Assist on and off explicitly
- Add a fallback: if notification cannot be confirmed delivered, log to a "missed interrupts" file and show a summary at the next manual launch
- Do not build the habit loop entirely on notifications — the CLI `run` command as a manual launch should be equally first-class
- `desktop-notifier` (by Samschott) is more actively maintained than `plyer` for Windows 11 in 2025 and handles async notification APIs correctly

**Phase to address:** Phase 2 (interrupt mode) — validate on target platform before shipping.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| SRS algorithm choice | SM-2 ease hell, review debt | Use FSRS; add daily review cap |
| Onboarding / first session | Cold start alienation | Placement quiz before first full session |
| Gamification design | Extrinsic rewards replace intrinsic motivation | XP tied to recall quality, not session count |
| AI question generation | Hallucinated answers, version staleness | Version-tagged prompts, user flagging, local cache |
| Interrupt scheduling | Notification fatigue, dismiss reflex | Long default interval, quiet hours, single-question format |
| Progress tracking | Activity metrics mask stagnation | Show accuracy trends and speed, not just counts |
| Content maintenance | Outdated DevOps questions | last_verified tagging + AI freshness layer |
| Windows notification | Silent delivery failures | Test with Focus Assist; add fallback detection |

---

## Sources

- [Why most Spaced Repetition Apps don't work and how to fix it](https://universeofmemory.com/spaced-repetition-apps-dont-work/)
- [Effective Spaced Repetition](https://borretti.me/article/effective-spaced-repetition)
- [FSRS Algorithm explained — RemNote Help Center](https://help.remnote.com/en/articles/9124137-the-fsrs-spaced-repetition-algorithm)
- [ABC of FSRS — open-spaced-repetition/fsrs4anki Wiki](https://github.com/open-spaced-repetition/fsrs4anki/wiki/abc-of-fsrs)
- [Alleviating the Cold Start Problem in Adaptive Learning — Springer](https://link.springer.com/article/10.1007/s42113-021-00101-6)
- [Large-scale evaluation of cold-start mitigation in adaptive fact learning — Springer](https://link.springer.com/article/10.1007/s11257-024-09401-5)
- [Eight Common Gamification Mistakes To Avoid — TalentLMS](https://www.talentlms.com/blog/common-gamification-mistakes-avoid/)
- [When Gamification Spoils Your Learning: A Qualitative Case — arXiv](https://arxiv.org/pdf/2203.16175)
- [Gamification is not Working: Why? — SAGE Journals](https://journals.sagepub.com/doi/10.1177/15554120241228125)
- [The Psychology Behind Duolingo's Streak Feature](https://www.justanotherpm.com/blog/the-psychology-behind-duolingos-streak-feature)
- [The Psychology of Hot Streak Game Design — UX Magazine](https://uxmag.com/articles/the-psychology-of-hot-streak-game-design-how-to-keep-players-coming-back-every-day-without-shame)
- [Design Guidelines For Better Notifications UX — Smashing Magazine](https://www.smashingmagazine.com/2025/07/design-guidelines-better-notifications-ux/)
- [App Push Notification Best Practices for 2026 — Appbot](https://appbot.co/blog/app-push-notifications-2026-best-practices/)
- [Anki Backlog Rescue: Settings, Habits, and Filters — MemoForge](https://memoforge.app/blog/beat-anki-overwhelm-settings-habits-clear-backlogs/)
- [Claude API Rate Limits — Official Docs](https://docs.claude.com/en/api/rate-limits)
- [desktop-notifier Python library — GitHub](https://github.com/samschott/desktop-notifier)
- [What I learned building an AI-driven spaced repetition app — Sean Goedecke](https://www.seangoedecke.com/autodeck/)
