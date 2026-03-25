---
name: qros-idea-intake-author
description: Use when a raw trading idea needs to be qualified before it is allowed to become a formal mandate.
---

# Idea Intake Author

## Purpose

把原始 idea 压成 `00_idea_intake` 的正式产物，而不是直接写 mandate。

## Required Outputs

- `idea_brief.md`
- `observation_hypothesis_map.md`
- `research_question_set.md`
- `scope_canvas.yaml`
- `qualification_scorecard.yaml`
- `idea_gate_decision.yaml`
- `artifact_catalog.md`

## Mandatory Discipline

- 必须先写 `observation`，再写 hypothesis
- 必须同时写 `primary hypothesis` 和 `counter-hypothesis`
- 必须写 machine-readable `qualification_scorecard.yaml`
- 必须写 machine-readable `idea_gate_decision.yaml`
- 不能直接宣布进入 train、backtest 或 shadow

## Qualification Dimensions

- `observability`
- `mechanism_plausibility`
- `tradeability`
- `data_feasibility`
- `scoping_clarity`
- `distinctiveness`

每一项都必须写：

- `score`
- `evidence`
- `uncertainty`
- `kill_reason`

## Gate Verdicts

- `GO_TO_MANDATE`
- `NEEDS_REFRAME`
- `DROP`

## Working Rules

1. 先把原始 idea 写成标准观察
2. 再写 primary hypothesis 与 counter-hypothesis
3. 再把问题收窄成市场、标的、周期、任务
4. 填写 `qualification_scorecard.yaml`
5. 产出 `idea_gate_decision.yaml`
6. 若 verdict 不是 `GO_TO_MANDATE`，停止，不得静默进入 mandate
