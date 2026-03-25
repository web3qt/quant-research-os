---
name: qros-research-session
description: Use when the user wants to start one orchestrated QROS conversation that drives idea_intake, mandate authoring, and mandate review from a single entry point.
---

# QROS Research Session

## Purpose

这是 QROS 的统一入口 skill。

目标不是让用户记住多个 skills 和脚本，而是：

- 从一个会话开始
- 自动识别或创建 lineage
- 自动判断当前 stage
- 自动推进 `idea_intake -> mandate -> mandate review`
- 只在缺关键信息或治理分歧时停下来问用户

## First-Wave Scope

第一版只覆盖：

- `idea_intake`
- `mandate`
- `mandate review`

明确不覆盖：

- `data_ready`
- `signal_ready`
- 更后续的 train/test/backtest/holdout/shadow

## Required Runtime

Use the orchestrator runtime:

- `python scripts/run_research_session.py --outputs-root outputs --raw-idea "<idea>"`
- `python scripts/run_research_session.py --outputs-root outputs --lineage-id "<lineage_id>"`

Reuse the deterministic runtime rather than improvising directory state in chat.

## Working Rules

1. Resolve or create the lineage
2. Detect the current stage from disk
3. Auto-scaffold `00_idea_intake/` when it does not exist
4. Drive `idea_intake` authoring with the same discipline as `qros-idea-intake-author`
5. If the intake gate reaches `GO_TO_MANDATE`, freeze mandate artifacts
6. Drive mandate completion with the same discipline as `qros-mandate-author`
7. When mandate artifacts are ready, move into mandate review
8. Reuse the same gate discipline as `qros-mandate-review`
9. Stop after `mandate review`; do not silently enter `data_ready`

## Auto vs Ask

Auto-act when:

- creating a lineage slug
- scaffolding `00_idea_intake/`
- building mandate artifacts after `GO_TO_MANDATE`
- detecting the current stage
- reporting current state

Ask the user only when:

- key research scope is missing
- counter-hypothesis is missing
- kill criteria are missing
- intake should become `NEEDS_REFRAME` or `DROP`
- a governance judgment must be made explicitly

## State Source Of Truth

Use disk artifacts as the primary state:

- `outputs/<lineage>/00_idea_intake/`
- `outputs/<lineage>/01_mandate/`
- mandate review closure artifacts

Do not rely on chat history alone to determine progress.

## Status Reporting

After each meaningful step, report:

- `lineage`
- `current_stage`
- `artifacts_written`
- `gate_status`
- `next_action`

## Guardrails

- Do not fabricate `review_findings.yaml`
- Do not bypass `idea_gate_decision.yaml`
- Do not bypass mandate review closure
- Do not claim `data_ready` is unlocked in v1

## Internal Discipline Sources

When writing or reviewing content, follow the same contracts as:

- `qros-idea-intake-author`
- `qros-mandate-author`
- `qros-mandate-review`
