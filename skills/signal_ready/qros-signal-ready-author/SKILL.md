---
name: qros-signal-ready-author
description: Use when reviewed data_ready outputs must be frozen into formal baseline-only signal_ready artifacts through grouped interactive confirmation.
---

# Signal Ready Author

## Purpose

只在 `data_ready review` closure 完成之后，把 `02_data_ready` 冻结成正式 `03_signal_ready` 产物。

这里的 `signal_ready` 不是静默跑参数搜索，而是交互式冻结“正式 baseline signal 合同”。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `03_signal_ready` 需要交付的 baseline signal timeseries、param 身份和 coverage 证据，而不是把空目录、placeholder 文件或只有合同语义的说明文档当作 signal_ready 完成。

## Required Inputs

- `02_data_ready/dataset_manifest.json`
- `02_data_ready/data_contract.md`
- `02_data_ready/artifact_catalog.md`
- `02_data_ready/field_dictionary.md`
- `02_data_ready/stage_completion_certificate.yaml`

## Required Outputs

- `param_manifest.csv`
- `params/`
- `signal_coverage.csv`
- `signal_coverage.md`
- `signal_coverage_summary.md`
- `signal_contract.md`
- `signal_fields_contract.md`
- `signal_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `signal_expression`
- `param_identity`
- `time_semantics`
- `signal_schema`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 data_ready 产物
- 第一版只允许冻结 baseline signal
- 不得产出 search batch 或 full frozen grid
- 必须在当前研究仓真实生成 baseline `param_id` 对应的时序产物、manifest 和 coverage 证据
- 空目录、placeholder `parquet/csv/md`、只有口头或文档语义说明的产物都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 signal_ready？`
- 不得静默修改 mandate 已冻结的核心机制边界

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。

## Gate Discipline

### Param ID 完整性声明
`param_manifest.csv` 必须列出**所有将被下游 Train/Test 消费的 param_id**。

- 下游阶段只允许消费已在本阶段显式物化过的 param_id
- 若 Train 或 Test 阶段引入了在本阶段从未物化过的 param_id，这是**硬性 fail**
- 冻结时必须问清楚：是否还有计划在 Train 阶段新增参数？若有，必须先回到 signal_ready 补物化

### Baseline-Only 约束
第一版 signal_ready 只允许冻结 baseline signal（1 个或极少数 baseline param_id）：
- 不得直接产出 full search batch 或 full frozen grid
- search batch 和 full grid 须等 baseline 完成并经 train review 后，方可在 signal_ready 新版本中追加

### Skipped Params 显式记录
若有 param_id 未成功物化（failed/skipped），必须在 `signal_coverage.md` 中单独列出：
- 每条 skipped 必须写原因
- skipped params > 0 时，verdict 最高为 `CONDITIONAL PASS`

### Signal Layer Field Coverage
`field_dictionary.md` 必须覆盖 `params/` 中实际 parquet 文件的字段名，不能只覆盖 mandate 层字段。冻结前检查：params 文件的每个列名是否都在 field_dictionary 中有条目？

## Working Rules

1. 确认 `02_data_ready/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `signal_expression`
3. 再收敛并确认 `param_identity`；核查 param_manifest 是否覆盖所有下游将消费的 param_id
4. 再收敛并确认 `time_semantics`
5. 再收敛并确认 `signal_schema`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 signal timeseries、param manifest、coverage 证据和字段合同
8. 输出一份 grouped signal_ready summary
9. 只有用户最终批准后，才生成正式 `03_signal_ready` artifacts
10. 验证 field_dictionary 覆盖 params/ 实际字段
11. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
12. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 signal_ready 完成
