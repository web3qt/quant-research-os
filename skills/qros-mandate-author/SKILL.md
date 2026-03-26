---
name: qros-mandate-author
description: Use when a qualified idea has passed intake gate and must be frozen into formal mandate artifacts.
---

# Mandate Author

## Purpose

只在 `GO_TO_MANDATE` 条件下，把 `00_idea_intake` 产物冻结成正式 `01_mandate` 产物。

这里的 `mandate` 不是静默补文档，而是交互式冻结研究合同。

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

## Freeze Groups

必须按 4 组推进：

- `research_intent`
- `scope_contract`
- `data_contract`
- `execution_contract`

## Mandatory Discipline

- 只能消费已经通过 qualification 的 intake artifacts
- 必须冻结研究主问题、scope、时间切分、参数边界和实现栈
- 必须先确认 `data_source` 与 `bar_size`，再冻结 mandate
- 必须写清 success / failure / budget / excluded scope
- 每一组都要先回显 freeze draft，再确认该组
- 四组全部确认后，才允许最终 `是否确认进入 mandate`
- 禁止 post-hoc restatement
- 禁止根据后验结果静默改题

## Working Rules

1. 读取 `idea_gate_decision.yaml`
2. 确认 verdict = `GO_TO_MANDATE`
3. 先收敛并确认 `research_intent`
4. 再收敛并确认 `scope_contract`
5. 再收敛并确认 `data_contract`
6. 再收敛并确认 `execution_contract`
7. 输出一份 grouped freeze summary
8. 只有用户最终批准后，才生成正式 mandate artifacts
9. 将 confirmed freeze groups 压成 `mandate.md`、`research_scope.md`
10. 生成 `time_split.json`、`parameter_grid.yaml`、`run_config.toml`
11. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
