# Feature Landscape: HackMySkills

**Domain:** CLI-based DevOps skill trainer with spaced repetition and habit-forming mechanics
**Researched:** 2026-03-13
**Overall confidence:** HIGH (gamification/SRS), MEDIUM (DevOps-specific content types)

---

## Table Stakes

Features users expect from any spaced repetition or habit-forming learning tool. Missing any of these and users will quit or reach for Anki instead.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Spaced repetition scheduling | Core retention mechanism — without it you're just a random quiz app | Medium | FSRS is the modern standard; SM-2 is acceptable fallback |
| Persistent progress across sessions | Users need to feel state is never lost | Low | Local SQLite or JSON file; must survive crashes |
| Daily streak counter | Streak of 7+ days correlates to 3.6x course completion rate (Duolingo data) | Low | Single most important habit-forming mechanic |
| "Did today's review" indicator | Users need to know at a glance if they're done for the day | Low | Binary completed/pending — reduces cognitive load |
| Per-topic performance tracking | Weak areas surface prominently; users see real improvement | Medium | Card-level difficulty history, topic-level aggregate |
| Graceful failure recovery | Users miss a day — the app must not punish them into quitting | Low | See streak mercy mechanic in differentiators |
| Session completion feedback | Immediate dopamine hit after finishing a review set | Low | ASCII art, a short summary line, a ding — anything |
| Configurable question bank | If content cannot be edited without touching code, power users flee | Low | YAML or JSON question files, topic-scoped |
| Multiple question formats | Pure flashcard gets boring; needs variety to maintain attention | Medium | At minimum: Q&A recall, command fill-in, multiple choice |
| Session time estimate | "5 cards left (~2 min)" — removes anxiety about how long it takes | Low | Based on rolling average of seconds-per-card |

---

## Differentiators

Features that separate HackMySkills from Anki + a DevOps deck. These are the "why not just use Anki?" answers.

### D1: FSRS Algorithm (Not SM-2)

**Value:** 20–30% fewer reviews for the same retention target. FSRS-6 outperforms SM-2 for 99.6% of users by log-loss metric. Trained on 700M real reviews.

**Implementation:** `py-fsrs` — official Python package, actively maintained, PyPI-available, minimal API surface.

```python
from fsrs import Scheduler, Card, Rating
scheduler = Scheduler()
card = Card()
card, review_log = scheduler.review_card(card, Rating.Good)
```

**Complexity:** Low (library handles everything). Configurable desired retention rate (default 0.9 is good; allow 0.7–0.95 user override).

**Confidence:** HIGH — verified via py-fsrs official repo and Anki forum benchmarks.

---

### D2: Interrupt Mode (Background Poller / System Notification)

**Value:** The Duolingo habit loop works because it meets users where they are. For a DevOps engineer sitting in a terminal all day, a random quiz popup at 10:30 AM and 2:15 PM is worth 10 "remember to study tonight" reminders.

**What to build:**
- A background process (or OS scheduled task) that fires a system notification or directly invades the terminal at configurable intervals
- On click/activation: opens a micro-session of 1–3 cards
- On Windows: `plyer` or `win10toast` for toast notifications; alternatively direct terminal output via a cron-style scheduler

**Key insight from research:** Duolingo times notifications based on *when you usually learn*, not random. Start with user-configurable time windows (e.g., "9-11am and 2-4pm"), not truly random.

**Complexity:** Medium — background process lifecycle on Windows (Task Scheduler vs. running daemon) has edge cases.

**Confidence:** MEDIUM — interrupt pattern is validated; Windows-specific implementation needs prototyping.

---

### D3: Streak Mercy Mechanic ("Streak Freeze")

**Value:** Duolingo's research showed separating streaks from daily goals increased 7-day streak retention by 40%. A single missed day that kills a 30-day streak causes users to quit entirely.

**What to build:**
- "Streak freeze" that auto-activates if you were active yesterday and today is a non-review day
- Grace period: session completed before 2 AM counts for the prior day
- Explicit freeze item earned via consistency (e.g., every 7-day streak = 1 earned freeze)
- Maximum 1 auto-freeze per rolling 7 days — prevents the mechanic from becoming meaningless

**What NOT to build:** Purchasable streak freezes (dark pattern, creates pay-to-win feel in a personal tool).

**Complexity:** Low.

**Confidence:** HIGH — streak freeze effectiveness is extensively documented via Duolingo A/B testing.

---

### D4: Adaptive Difficulty Ladder

**Value:** Spaced repetition handles *when* to review; adaptive difficulty handles *what kind of question* to ask. A user who answers "What is a Kubernetes Pod?" correctly 5 times should get scenario-based questions, not definition recalls.

**What to build:**
- Per-topic mastery score (0–100) derived from FSRS card stability metrics
- Question difficulty tiers: Recall (L1) → Application (L2) → Scenario/Edge Case (L3)
- When a topic's mastery crosses a threshold, unlock L2/L3 questions for it
- New topics always start at L1 regardless of user's overall level

**Complexity:** Medium — requires question bank to be tagged by tier, plus threshold logic.

**Confidence:** MEDIUM — adaptive difficulty is well-researched generally; tier-to-mastery mapping is an architectural decision, not research-validated.

---

### D5: AI-Generated Question Expansion (Claude API)

**Value:** The static question bank has a ceiling. Users who've seen all 200 Kubernetes questions need novelty. Claude can generate new questions against a topic + difficulty tier on demand, then have them reviewed before entering the permanent pool.

**What to build:**
- On-demand generation: "Generate 5 new Hard questions for topic: terraform-state"
- Generated questions enter a "pending review" pool, not live rotation immediately
- User can approve/reject generated questions after attempting them
- Approved questions merge into the local question bank

**Anti-pattern to avoid:** Auto-injecting AI questions without validation. Low-quality or wrong questions corrupt the learning signal.

**Complexity:** Medium — Claude API call is simple; the review-and-approval UX is the work.

**Confidence:** MEDIUM — Claude API usage is straightforward; question quality control UX needs validation.

---

### D6: DevOps-Specific Question Formats

**Value:** Anki treats all knowledge as equal. DevOps knowledge is heavily procedural and contextual. Standard Q&A flashcards are weakest for procedural knowledge.

**Recommended content types, ranked by learning value for DevOps:**

| Format | Learning Value | Example | Complexity |
|--------|---------------|---------|------------|
| Command fill-in | High — matches real usage | `kubectl ___ pods -n kube-system` | Medium |
| Scenario → diagnosis | High — mirrors real incidents | "Pod is CrashLoopBackOff. First 3 commands?" | High |
| Flag/option recall | High — catches common gaps | "What flag to `kubectl apply` enables server-side apply?" | Low |
| Concept definition recall | Medium — baseline knowledge | "What is a PodDisruptionBudget?" | Low |
| Multiple choice | Medium — works for "which is correct" facts | "Which IAM policy action allows S3 ListBucket?" | Low |
| Error → cause matching | High — maps to real incident response | Show a Terraform error, identify root cause | Medium |
| Sequence ordering | Medium — CI/CD pipeline stages, Terraform plan order | Drag-to-order doesn't apply in CLI; use numbered input | Medium |

**CLI implementation note:** Command fill-in in a terminal should use `_` as the blank marker and accept substring matches plus exact matches. Fuzzy matching on command answers reduces frustration.

**Content domains to cover (initial bank):**
- Kubernetes: pod lifecycle, resource types, kubectl commands, RBAC, networking, storage
- Terraform: state management, resource types, provider config, workspace, import/taint
- CI/CD: pipeline stages, GitHub Actions syntax, deployment strategies
- Bash: common patterns, pipes, process management, string manipulation
- AWS/Cloud: IAM, VPC, ECS, S3, CloudWatch, core concepts

---

### D7: XP System Tied to Real Learning Events

**Value:** XP that's decoupled from actual mastery becomes a vanity metric users learn to ignore. XP that maps to genuine learning milestones creates meaningful progression.

**What to build:**
- XP awarded only for review completion (not for opening the app)
- Bonus XP multipliers: streak length, difficulty tier answered correctly, topic first-mastered
- XP not awarded for reviewing cards you've had on "easy" for 90+ days — prevents grinding familiar cards for points
- Level thresholds should follow an exponential curve so early levels feel fast (dopamine), later levels feel earned
- Level names tied to the domain: "kubectl Apprentice" → "SRE Journeyman" → "Platform Architect"

**What to avoid:** Leaderboards (the project is explicitly solo), daily login bonuses not tied to learning, XP for generating/deleting cards.

**Complexity:** Low.

**Confidence:** HIGH — XP/level design principles are well-documented; domain-specific naming is a product decision.

---

### D8: Session Modes

**Value:** Different contexts demand different session shapes. A 2-minute interrupt during a meeting is different from a 20-minute focused drill.

| Mode | Duration | Card Count | Selection Logic |
|------|----------|------------|-----------------|
| Interrupt (micro) | 1–3 min | 3–5 cards | Due today + weakest topics |
| Daily review | 10–15 min | 15–25 cards | All due + a few new |
| Deep dive (topic) | 20–30 min | 30–50 cards | Single topic, all tiers |
| Weak spot drill | 10 min | 10–15 cards | Cards rated Again/Hard most recently |
| New material intro | 5–10 min | 10 new cards | Topics not yet started |

**Key insight:** The "daily review" mode should be completable in under 15 minutes. Research shows 10–15 min first sessions drive the best Day 7 retention. If the daily queue gets above ~25 cards, show a warning and offer to defer non-critical cards.

**Complexity:** Low (modes are just different card selection queries + session length caps).

---

## Anti-Features

Features to deliberately NOT build, and why.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Purchasable streak freezes | Dark pattern — monetizes anxiety around losing progress | Earn freezes through consistency (earned, not bought) |
| Social leaderboards / friend comparison | Project is explicitly solo-use; competition pressure can shift focus from mastery to gaming the score | XP/levels are purely personal progress indicators |
| Infinite daily queues (no cap) | Users presented with 80-card review backlogs quit | Cap daily session at ~25 cards; surface a "backlog warning" if reviews pile up |
| Auto-injecting unreviewed AI questions | Wrong AI-generated questions corrupt the learning signal; user loses trust in the tool | All AI questions enter a "pending" pool; user approves before they go live |
| Mandatory onboarding quiz (placement test) | Friction that kills Day 1 retention | Start with beginner cards for all topics; let FSRS sort difficulty naturally |
| Pop-up-style forced interrupts that block work | "Not annoying" is a core requirement; intrusive interrupts cause users to disable the tool | System notification + opt-in; user sets time windows; always dismissable |
| Gamified "lives" / health systems | Penalizing wrong answers with resource depletion increases anxiety and reduces honest recall attempts | Wrong answers just schedule the card for sooner review; no penalty beyond that |
| Spaced repetition on-rails (fixed track) | Users should be able to add topics, skip topics, and adjust content without code changes | Content in YAML/JSON files; topic enable/disable toggle |
| Overly complex XP curves | If users can't mentally predict how XP accumulates, it loses motivational value | Simple rule: N XP per card reviewed, bonus multiplier for difficulty tier and streak |
| Multi-device sync (MVP) | Adds backend infrastructure complexity with no immediate user value for a solo-user tool | Local SQLite first; export/import as sync solution if needed later |

---

## Feature Dependencies

```
FSRS algorithm ──────────────────► Card scheduling (everything depends on this)
Card scheduling ─────────────────► Streak tracking (needs "did review today" signal)
Streak tracking ─────────────────► Streak freeze mechanic
Question bank (tiered) ──────────► Adaptive difficulty ladder
Adaptive difficulty ladder ──────► Per-topic mastery score
Per-topic mastery score ─────────► XP system (XP quality depends on mastery signal)
Session modes ───────────────────► Interrupt mode (micro-session is just a very short daily review)
Claude API integration ──────────► AI question generation (requires question bank format to be stable first)
Question bank format (stable) ───► AI question approval flow
```

---

## MVP Recommendation

**Build first (MVP — validates the core habit loop):**

1. FSRS scheduling via `py-fsrs` with persistent local storage
2. Daily review session mode with session completion feedback
3. Streak counter + streak freeze (day grace period only, no freeze items yet)
4. Static question bank in YAML: Kubernetes + Terraform, L1 recall + command fill-in
5. Per-topic performance summary after each session
6. XP counter with level label (no complex curve — flat 10 XP/card is fine for MVP)

**Defer until MVP is validated:**

- Interrupt mode / background poller (technically complex, validate habit loop without it first)
- AI question generation (adds Claude API dependency; validate content quality of static bank first)
- Adaptive difficulty tiers (need enough static L2/L3 questions to make it worth building)
- Deep dive and weak spot session modes (nice-to-have; daily review covers the need initially)
- Streak freeze earn/spend mechanic (grace period is enough for MVP)

**Never build (confirmed anti-features):**

- Social features, purchasable anything, forced interrupts, uncapped daily queues

---

## Sources

- [FSRS vs SM-2 comparison — MemoForge Blog](https://memoforge.app/blog/fsrs-vs-sm2-anki-algorithm-guide-2025/)
- [FSRS benchmark — Expertium's Blog](https://expertium.github.io/Benchmark.html)
- [py-fsrs official Python implementation](https://github.com/open-spaced-repetition/py-fsrs)
- [py-fsrs on PyPI](https://pypi.org/project/fsrs/2.1.1/)
- [Duolingo streak system breakdown](https://medium.com/@salamprem49/duolingo-streak-system-detailed-breakdown-design-flow-886f591c953f)
- [Duolingo gamification case study 2025](https://www.youngurbanproject.com/duolingo-case-study/)
- [How Duolingo streak builds habit — official Duolingo blog](https://blog.duolingo.com/how-duolingo-streak-builds-habit/)
- [Duolingo gamification secrets — Orizon](https://www.orizon.co/blog/duolingos-gamification-secrets)
- [Streak mechanics for gamification — Plotline](https://www.plotline.so/blog/streaks-for-gamification-in-mobile-apps)
- [Psychology of hot streak game design — UX Magazine](https://uxmag.com/articles/the-psychology-of-hot-streak-game-design-how-to-keep-players-coming-back-every-day-without-shame)
- [Dark patterns in gamification — ResearchGate](https://www.researchgate.net/publication/339487229_Gamification_for_Good_Addressing_Dark_Patterns_in_Gamified_UX_Design)
- [Gamification XP experience points — Growth Engineering](https://www.growthengineering.co.uk/gamification-experience-points/)
- [Level systems and progression design — Medium (KJH)](https://mybaseball52.medium.com/how-to-design-level-system-with-gamification-concepts-b4e93d87fcf4)
- [Adaptive learning systems — Eduonix Blog](https://blog.eduonix.com/2026/03/adaptive-learning-systems-skill-progression/)
- [Session length and Day 7 retention benchmarks — Adjust](https://www.adjust.com/blog/app-sessions/)
- [CLI spaced repetition tools — GitHub Topics](https://github.com/topics/spaced-repetition?l=go)
- [KodeKloud Terraform challenges — interactive CLI learning](https://kodekloud.com/courses/terraform-challenges)
