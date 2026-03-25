---
name: qros-signal-ready-author
description: Use when reviewed data_ready outputs must be frozen into formal baseline-only signal_ready artifacts through grouped interactive confirmation.
---

# Signal Ready Author

## Purpose

只在 `data_ready review` closure 完成之后，把 `02_data_ready` 冻结成正式 `03_signal_ready` 产物。

这里的 `signal_ready` 不是静默跑参数搜索，而是交互式冻结“正式 baseline signal 合同”。

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
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 signal_ready？`
- 不得静默修改 mandate 已冻结的核心机制边界

## Working Rules

1. 确认 `02_data_ready/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `signal_expression`
3. 再收敛并确认 `param_identity`
4. 再收敛并确认 `time_semantics`
5. 再收敛并确认 `signal_schema`
6. 最后确认 `delivery_contract`
7. 输出一份 grouped signal_ready summary
8. 只有用户最终批准后，才生成正式 `03_signal_ready` artifacts
9. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
