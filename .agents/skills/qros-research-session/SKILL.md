---
name: qros-research-session
description: Use when the user wants to start one orchestrated QROS conversation that drives idea_intake, mandate authoring, mandate review, data_ready authoring, data_ready review, signal_ready authoring, and signal_ready review from a single entry point.
---

# QROS Research Session

## Purpose

这是 QROS 的统一入口 skill。

目标不是让用户记住多个 skills 和脚本，而是：

- 从一个会话开始
- 自动识别或创建 lineage
- 自动判断当前 stage
- 显式推进 `idea_intake -> mandate_confirmation_pending -> mandate -> mandate review -> data_ready_confirmation_pending -> data_ready -> data_ready review -> signal_ready_confirmation_pending -> signal_ready -> signal_ready review`
- 只在缺关键信息或治理分歧时停下来问用户

## First-Wave Scope

第一版只覆盖：

- `idea_intake`
- `mandate`
- `mandate review`
- `data_ready`
- `data_ready review`
- `signal_ready`
- `signal_ready review`

明确不覆盖：

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
17. After mandate review closure, enter `data_ready_confirmation_pending`
18. Confirm `extraction_contract`
19. Confirm `quality_semantics`
20. Confirm `universe_admission`
21. Confirm `shared_derived_layer`
22. Confirm `delivery_contract`
23. Show one final data_ready summary
24. Ask the user one explicit question: `是否按以上内容冻结 data_ready？`
25. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_DATA_READY` and freeze data_ready artifacts
26. Drive data_ready completion with the same discipline as `qros-data-ready-author`
27. When data_ready artifacts are ready, move into data_ready review
28. Reuse the same gate discipline as `qros-data-ready-review`
29. After data_ready review closure, enter `signal_ready_confirmation_pending`
30. Confirm `signal_expression`
31. Confirm `param_identity`
32. Confirm `time_semantics`
33. Confirm `signal_schema`
34. Confirm `delivery_contract`
35. Show one final signal_ready summary
36. Ask the user one explicit question: `是否按以上内容冻结 signal_ready？`
37. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_SIGNAL_READY` and freeze signal_ready artifacts
38. Drive signal_ready completion with the same discipline as `qros-signal-ready-author`
39. When signal_ready artifacts are ready, move into signal_ready review
40. Reuse the same gate discipline as `qros-signal-ready-review`
41. Stop after `signal_ready review`; do not silently enter `train_calibration`

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
- a governance judgment must be made explicitly, especially `CONFIRM_MANDATE`, `CONFIRM_DATA_READY`, `CONFIRM_SIGNAL_READY`, `HOLD`, or `REFRAME`

When the stage is `mandate_confirmation_pending`, the agent must ask explicitly:

- `research_intent` 这一组冻结什么？
- `scope_contract` 这一组冻结什么？
- `data_contract` 这一组冻结什么？这里必须明确数据来源和 `bar_size`
- `execution_contract` 这一组冻结什么？
- 每组回显当前 freeze draft，并单独确认
- `是否确认进入 mandate？`

Do not skip this question. Do not imply the transition already happened.

When the stage is `data_ready_confirmation_pending`, the agent must ask explicitly:

- `extraction_contract` 这一组冻结什么？
- `quality_semantics` 这一组冻结什么？
- `universe_admission` 这一组冻结什么？
- `shared_derived_layer` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 data_ready？`

Do not skip this question. Do not imply the transition already happened.

When the stage is `signal_ready_confirmation_pending`, the agent must ask explicitly:

- `signal_expression` 这一组冻结什么？
- `param_identity` 这一组冻结什么？
- `time_semantics` 这一组冻结什么？
- `signal_schema` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 signal_ready？`

Do not skip this question. Do not imply the transition already happened.

## State Source Of Truth

Use disk artifacts as the primary state:

- `outputs/<lineage>/00_idea_intake/`
- `outputs/<lineage>/01_mandate/`
- `outputs/<lineage>/02_data_ready/`
- `outputs/<lineage>/03_signal_ready/`
- mandate review closure artifacts
- data_ready review closure artifacts
- signal_ready review closure artifacts

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
- Do not bypass `data_ready_transition_approval.yaml`
- Do not bypass `signal_ready_transition_approval.yaml`
- Do not bypass mandate review closure
- Do not bypass data_ready review closure
- Do not bypass signal_ready review closure
- Do not claim `train_calibration` is unlocked in v1
- Do not require the user to type backend flags or internal runtime commands during the primary chat workflow

## Internal Discipline Sources

When writing or reviewing content, follow the same contracts as:

- `qros-idea-intake-author`
- `qros-mandate-author`
- `qros-mandate-review`
- `qros-data-ready-author`
- `qros-data-ready-review`
- `qros-signal-ready-author`
- `qros-signal-ready-review`
