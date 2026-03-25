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

- 不能只根据用户一句原始 idea 就直接替用户补完整 qualification 结论
- 必须先进行一轮显式 intake 访谈，再允许写 `qualification_scorecard.yaml` 和 `idea_gate_decision.yaml`
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

1. 先问清并回显 `observation`
2. 再问清并回显 `primary hypothesis` 与 `counter-hypothesis`
3. 再问清并回显 `market`、`universe`、`target_task`
4. 再问清并回显 `data_source`、`bar_size`
5. 再问清并回显 `kill criteria` 或 `reframe` 条件
6. 在用户回答这些关键问题前，不得替用户静默填写完整 qualification 分数和 gate verdict
7. 只有在 intake 信息足够后，才填写 `qualification_scorecard.yaml`
8. 然后产出 `idea_gate_decision.yaml`
9. 若 verdict 不是 `GO_TO_MANDATE`，停止，不得静默进入 mandate
