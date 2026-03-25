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
- 显式推进 `idea_intake -> mandate_confirmation_pending -> mandate -> mandate review`
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

The user should not need to remember internal commands. Runtime commands are backend mechanics for the agent, debugging, and manual recovery.

## Working Rules

1. Resolve or create the lineage
2. Detect the current stage from disk
3. Auto-scaffold `00_idea_intake/` when it does not exist
4. Drive `idea_intake` authoring with the same discipline as `qros-idea-intake-author`
5. If the intake gate reaches `GO_TO_MANDATE`, stop at `mandate_confirmation_pending`
6. Start a grouped mandate freeze conversation instead of silently writing `01_mandate`
7. Confirm `research_intent`
8. Confirm `scope_contract`
9. Confirm `data_contract`, especially 数据来源哪里来 and what `bar_size` is frozen, for example `1m`, `5m`, or `15m`
10. Confirm `execution_contract`
11. Show one final mandate summary
12. Ask the user one explicit question: `是否确认进入 mandate？`
13. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_MANDATE` and freeze mandate artifacts
14. Drive mandate completion with the same discipline as `qros-mandate-author`
15. When mandate artifacts are ready, move into mandate review
16. Reuse the same gate discipline as `qros-mandate-review`
17. Stop after `mandate review`; do not silently enter `data_ready`

## Auto vs Ask

Auto-act when:

- creating a lineage slug
- scaffolding `00_idea_intake/`
- detecting the current stage
- reporting current state

Ask the user only when:

- key research scope is missing
- counter-hypothesis is missing
- kill criteria are missing
- intake should become `NEEDS_REFRAME` or `DROP`
- a governance judgment must be made explicitly, especially `CONFIRM_MANDATE`, `HOLD`, or `REFRAME`

When the stage is `mandate_confirmation_pending`, the agent must ask explicitly:

- `research_intent` 这一组冻结什么？
- `scope_contract` 这一组冻结什么？
- `data_contract` 这一组冻结什么？这里必须明确数据来源和 `bar_size`
- `execution_contract` 这一组冻结什么？
- 每组回显当前 freeze draft，并单独确认
- `是否确认进入 mandate？`

Do not skip this question. Do not imply the transition already happened.

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
- `why_now`
- `open_risks`

## Guardrails

- Do not fabricate `review_findings.yaml`
- Do not bypass `idea_gate_decision.yaml`
- Do not bypass `mandate_transition_approval.yaml`
- Do not bypass mandate review closure
- Do not claim `data_ready` is unlocked in v1
- Do not require the user to type backend flags or internal runtime commands during the primary chat workflow

## Internal Discipline Sources

When writing or reviewing content, follow the same contracts as:

- `qros-idea-intake-author`
- `qros-mandate-author`
- `qros-mandate-review`
