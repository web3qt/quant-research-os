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

## Counter-Hypothesis Validation

`counter_hypothesis` 必须是**机制层面的对立解释**，不是 primary hypothesis 的弱化版。

- ❌ 不合格："传导效果较弱"
- ✅ 合格："只是共同 beta 暴露，不存在可交易的滞后机制"

写完 counter_hypothesis 后，必须显式核查：它是否提出了与 primary hypothesis 在机制层面**不可调和**的解释？若只是程度差异，必须要求重写。

## Kill Criteria Validation

`kill_criteria` 必须是**在 intake 阶段不看数据就能评估的条件**。

- ❌ 不合格："如果结果不好就停止"
- ✅ 合格："若观测变量无法稳定定义，则停止"

写完 kill_criteria 后，必须显式核查：这条标准是否依赖真实数据结果？若依赖结果才能评估，必须要求重写。

## NEEDS_REFRAME Discipline

- 若 verdict = `NEEDS_REFRAME`，不得把"修改几行文字"等同于重新 qualification
- 必须从步骤 2（intake 访谈）重新走，重新产出所有 intake artifacts，再重新给出新的 `idea_gate_decision.yaml`
- 只有完整重走后，才允许给出新的 `GO_TO_MANDATE`

## Audit vs. Formal Gate Separation

- Qualification scorecard 的评分和 `idea_gate_decision.yaml` 的 verdict 只由 6 个 formal gate 条件决定
- 访谈过程中发现的文档风格、命名方式等问题属于 audit-only，**不得**用于阻断 formal gate verdict
- `idea_gate_decision.yaml` 的 `why` 字段只写 formal gate 通过/失败的原因，不写 audit 发现

## Working Rules

1. 先问清并回显 `observation`
2. 再问清并回显 `primary hypothesis` 与 `counter-hypothesis`；核查 counter_hypothesis 是否是机制层面对立（见上）
3. 再问清并回显 `market`、`universe`、`target_task`
4. 再问清并回显 `data_source`、`bar_size`
5. 再问清并回显 `kill criteria`；核查 kill_criteria 是否可在 intake 阶段评估（见上）
6. 在用户回答这些关键问题前，不得替用户静默填写完整 qualification 分数和 gate verdict
7. 只有在 intake 信息足够后，才填写 `qualification_scorecard.yaml`
8. 然后产出 `idea_gate_decision.yaml`
9. 若 verdict = `NEEDS_REFRAME`，告知需完整重走步骤 2-8，不得静默升格
10. 若 verdict = `DROP`，停止，不得静默进入 mandate
11. 只有 `GO_TO_MANDATE` 且 `approved_scope` 非空时，才允许提示进入 mandate 确认流程
