# HackMySkills

## What This Is

A CLI-based DevOps skill trainer that drills knowledge through spaced repetition, adaptive difficulty, and a habit-forming reward system. Think Duolingo for DevOps engineers — consistent, non-annoying learning interrupts throughout the day plus focused deep-dive sessions. Starts with DevOps skills (Kubernetes, Terraform, CI/CD, bash, cloud) and is designed to expand to other skill tracks over time.

## Core Value

The habit forms: the user gets quizzed consistently, sees their streak grow, and notices they're actually getting faster and more confident on topics they used to struggle with.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] CLI tool that runs on Windows (and cross-platform)
- [ ] Spaced repetition algorithm surfaces weak areas more frequently
- [ ] Adaptive difficulty — starts easy, gets harder as the user improves
- [ ] Reward/streak/XP system for dopamine feedback loop
- [ ] Habit-forming: scheduled or random popup-style interrupts throughout the day
- [ ] Focused session mode: deep-dive practice on demand
- [ ] Multiple content types: flashcards, scenarios, command fill-in, explain-the-concept
- [ ] Curated DevOps question bank (Kubernetes, Terraform, CI/CD, bash, AWS/cloud)
- [ ] AI-generated questions via Claude to fill gaps and add variety
- [ ] Extensible: new skill tracks can be added by editing config/content files
- [ ] Progress tracking: history of performance per topic over time

### Out of Scope

- Mobile app — web/CLI first
- Multi-user / social features — solo tool for now
- GUI/web interface — CLI is the primary interface (system notifications are OK as interrupts)

## Context

- User is a DevOps engineer on Windows 11, comfortable in the terminal
- Repo name is `hackmyskills` — gamified/hacking angle to learning
- Inspiration: Duolingo's habit loop (streaks, rewards, adaptive pacing) but not annoying
- Claude API available for AI-generated question content
- Skills to cover initially: Kubernetes, Terraform, CI/CD pipelines, bash scripting, AWS/cloud fundamentals, IaC concepts
- Future expansion: other engineering skills beyond DevOps

## Constraints

- **Platform**: Windows 11 primary, cross-platform preferred — Python or Node.js likely
- **Interface**: CLI-first; system notifications OK for interrupt mode
- **AI**: Claude API for dynamic question generation
- **Extensibility**: Content in editable files so user can add topics without touching code

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI-first interface | Fits naturally in a DevOps workflow | — Pending |
| Spaced repetition + adaptive difficulty | Best combo for retention + dopamine | — Pending |
| Curated bank + AI generation | Guarantees quality baseline + infinite variety | — Pending |

---
*Last updated: 2026-03-13 after initialization*
