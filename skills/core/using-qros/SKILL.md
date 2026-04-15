---
name: using-qros
description: Use when the user mentions quantitative research, factor research, alpha research, backtesting, signal construction, or any systematic trading research workflow that needs structured stage-gated discipline.
---

# Using QROS

You have **QROS (Quant Research OS)** — a stage-gated quantitative research workflow framework.

QROS turns raw trading ideas into validated alpha through formal freeze gates, review discipline, and lineage tracking.

## When to Activate QROS

Before responding to any request, check if it matches QROS triggers:

**Auto-trigger when user mentions:**
- "research this idea" / "help me study" / "quantitative research"
- Factor construction, signal design, alpha generation
- Backtesting, walk-forward, holdout validation
- Any systematic trading workflow that needs rigor
- "qros" explicitly

**Do NOT trigger for:**
- Generic coding questions unrelated to quant research
- One-off data analysis without research intent
- Questions about QROS itself (just answer normally)

## Activation Flow

```
User message → QROS trigger detected?
├─ Yes → Invoke qros-research-session skill via Skill tool
│        → Follow qros-research-session working rules
│        → Do NOT improvise outside the workflow
└─ No  → Respond normally without QROS
```

## Available Skills

### Entry Point
- **qros-research-session** — Unified research session covering all stages from idea intake to holdout validation

### Author Skills (stage artifact creation)
- **qros-idea-intake-author** — Structured idea qualification with hypothesis, counter-hypothesis, kill criteria
- **qros-mandate-author** — Freeze research contract: scope, time split, parameter grid, execution stack
- **qros-data-ready-author** — Freeze data extraction contract, quality semantics, universe admission
- **qros-signal-ready-author** — Freeze signal expression, param identity, time semantics
- **qros-train-freeze-author** — Freeze window contract, threshold contract, quality filters
- **qros-test-evidence-author** — Freeze formal gate contract, admissibility, audit trail
- **qros-backtest-ready-author** — Freeze execution policy, portfolio policy, risk overlay
- **qros-holdout-validation-author** — Freeze reuse contract, drift audit, failure governance

### Review Skills (stage gate verification)
- **qros-mandate-review** — Verify mandate freeze completeness and downstream permissions
- **qros-data-ready-review** — Verify data contract materialization and coverage
- **qros-signal-ready-review** — Verify signal schema, param governance
- **qros-train-freeze-review** — Verify threshold discipline and param isolation
- **qros-test-evidence-review** — Verify independent-sample statistics and admissibility
- **qros-backtest-ready-review** — Verify dual-engine outputs and capacity evidence
- **qros-holdout-validation-review** — Verify out-of-sample integrity

### Failure Handling
- **qros-stage-failure-handler** — Route review failures to stage-specific failure skills
- **qros-data-ready-failure** — data_ready stage failure classification and triage
- **qros-signal-ready-failure** — signal_ready stage failure classification and triage
- **qros-train-freeze-failure** — train_freeze stage failure classification and triage
- **qros-test-evidence-failure** — test_evidence stage failure classification and triage
- **qros-backtest-failure** — backtest_ready stage failure classification and triage
- **qros-holdout-failure** — holdout_validation stage failure classification and triage
- **qros-lineage-change-control** — Change control for scope/split/universe modifications

## Core Principles

1. **Freeze before build** — Every stage must be formally frozen before work begins
2. **Review before advance** — Every stage must pass review before the next stage starts
3. **No silent modifications** — Post-hoc changes require explicit change control or child lineage
4. **Evidence over claims** — Never accept empty directories, placeholder files, or contract-only markdown as completed work
5. **Disk is truth** — Always check disk artifacts for current state, never rely on chat history alone

## Red Flags

If you catch yourself doing any of these, STOP and follow the skill instead:

| Red Flag | Correct Action |
|----------|---------------|
| Skipping intake interview to jump to mandate | Complete full idea_intake first |
| Writing test results before train_freeze | Freeze train thresholds first |
| Silently modifying mandate after seeing signals | Open child lineage instead |
| Treating empty directories as completed stage | Require actual materialized artifacts |
| Bypassing review to advance stage | Complete review gate first |
| Improvising workflow outside QROS discipline | Follow qros-research-session rules |
