---
name: qros-mandate-author
description: Use when a qualified idea has passed intake gate and must be frozen into formal mandate artifacts.
---

# Mandate Author

## Purpose

只在 `GO_TO_MANDATE` 条件下，把 `00_idea_intake` 产物冻结成正式 `01_mandate` 产物。

## Required Inputs

- `qualification_scorecard.yaml`
- `research_question_set.md`
- `scope_canvas.yaml`
- `idea_gate_decision.yaml`

## Admission Rule

只有当 `idea_gate_decision.yaml` 明确写出 `GO_TO_MANDATE`，才允许继续。

如果 verdict 是：

- `NEEDS_REFRAME`
- `DROP`

则不得生成 mandate artifacts。

## Required Outputs

- `mandate.md`
- `research_scope.md`
- `time_split.json`
- `parameter_grid.yaml`
- `run_config.toml`
- `artifact_catalog.md`
- `field_dictionary.md`

## Mandatory Discipline

- 只能消费已经通过 qualification 的 intake artifacts
- 必须冻结研究主问题、scope、时间切分、参数边界和实现栈
- 必须先确认 `data_source` 与 `bar_size`，再冻结 mandate
- 必须写清 success / failure / budget / excluded scope
- 禁止 post-hoc restatement
- 禁止根据后验结果静默改题

## Working Rules

1. 读取 `idea_gate_decision.yaml`
2. 确认 verdict = `GO_TO_MANDATE`
3. 若 `scope_canvas.yaml` 里的 `data_source` 或 `bar_size` 缺失，先向用户询问
4. 将 confirmed `data_source` 与 `bar_size` 写回冻结范围
5. 将 approved scope 压成 `research_scope.md`
6. 将 research question 与限制条件压成 `mandate.md`
7. 生成 `time_split.json`、`parameter_grid.yaml`、`run_config.toml`
8. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
