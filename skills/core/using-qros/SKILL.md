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

在 Codex 中，普通用户入口应写成 `$qros-research-session`。`$qros-progress` 是只读查询，`$qros-stage-display` 是显式展示 guidance。不要让用户直接执行底层脚本；底层 runtime 命令只作为 agent 的 backend mechanics、debugging 和 manual recovery。

stage-specific `$qros-*-author` / `$qros-*-review` 不是普通阶段跳转入口，也不是普通用户需要知道的入口。它们只作为高级/debug/manual recovery 协议，或由 `$qros-research-session` 在当前 stage 已匹配时内部复用。它们开始前必须先通过 repo-local `./.qros/bin/qros-check-stage-entry --stage <stage_id> --lane author|review`；失败时应回到 `$qros-research-session` 恢复 runtime `current_stage`，不能直接补 artifact 或起 reviewer。

```
User message → QROS trigger detected?
├─ Yes → Invoke $qros-research-session skill via Skill tool
│        → Follow qros-research-session working rules
│        → Do NOT improvise outside the workflow
└─ No  → Respond normally without QROS
```

## Available Skills

### Entry Point
- **$qros-research-session** — Unified research session covering all stages from mandate admission to TSS/CSF holdout validation
- **$qros-progress** — Read-only lineage progress lookup for current stage, blocking gate, and next action

### Advanced Author Skills (debug/manual recovery)
- **qros-mandate-author** — Freeze research contract: scope, time split, parameter grid, execution stack
- **qros-tss-data-ready-author** — TSS data foundation for `research_route = time_series_signal`
- **qros-tss-signal-ready-author** — TSS signal/event schema and param identity
- **qros-tss-train-freeze-author** — TSS train-only thresholds and variant governance
- **qros-tss-test-evidence-author** — TSS independent test evidence
- **qros-tss-backtest-ready-author** — TSS strategy/backtest execution evidence
- **qros-tss-holdout-validation-author** — TSS final holdout validation
- **qros-data-ready-author** — Freeze data extraction contract, quality semantics, universe admission
- **qros-signal-ready-author** — Freeze signal expression, param identity, time semantics
- **qros-train-freeze-author** — Freeze window contract, threshold contract, quality filters
- **qros-test-evidence-author** — Freeze formal gate contract, admissibility, audit trail
- **qros-backtest-ready-author** — Freeze execution policy, portfolio policy, risk overlay
- **qros-holdout-validation-author** — Freeze reuse contract, drift audit, failure governance

### Advanced Review Skills (debug/manual recovery)
- **qros-mandate-review** — Verify mandate freeze completeness and downstream permissions
- **qros-tss-data-ready-review** — Verify TSS data foundation and time-index artifacts
- **qros-tss-signal-ready-review** — Verify TSS signal/event schema and route inheritance
- **qros-tss-train-freeze-review** — Verify TSS train threshold discipline
- **qros-tss-test-evidence-review** — Verify TSS independent-sample direction/path evidence
- **qros-tss-backtest-ready-review** — Verify TSS backtest execution and ledger evidence
- **qros-tss-holdout-validation-review** — Verify TSS holdout integrity
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
- **qros-tss-train-freeze-failure** — tss_train_freeze route-specific failure classification and triage
- **qros-tss-test-evidence-failure** — tss_test_evidence route-specific failure classification and triage
- **qros-lineage-change-control** — Change control for scope/split/universe modifications

## Core Principles

1. **Freeze before build** — Every stage must be formally frozen before work begins
2. **Review before advance** — Every stage must pass review before the next stage starts
3. **No silent modifications** — Post-hoc changes require explicit change control or child lineage
4. **Evidence over claims** — Never accept empty directories, placeholder files, or contract-only markdown as completed work
5. **Disk is truth** — Always check disk artifacts for current state, never rely on chat history alone
6. **Route-specific names matter** — New `time_series_signal` lineages use `tss_*` stages; TSS is single-asset history predicting that asset's future path/direction, not cross-sectional ranking

## Red Flags

If you catch yourself doing any of these, STOP and follow the skill instead:

| Red Flag | Correct Action |
|----------|---------------|
| Skipping mandate admission to jump to formal mandate | Complete `mandate_admission` first |
| Writing test results before train_freeze | Freeze train thresholds first |
| Silently modifying mandate after seeing signals | Open child lineage instead |
| Treating empty directories as completed stage | Require actual materialized artifacts |
| Bypassing review to advance stage | Complete review gate first |
| Improvising workflow outside QROS discipline | Follow qros-research-session rules |
