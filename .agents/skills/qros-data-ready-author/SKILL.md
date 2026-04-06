---
name: qros-data-ready-author
description: Use when a reviewed mandate must be frozen into formal data_ready artifacts through grouped interactive confirmation.
---

# Data Ready Author

## Purpose

只在 `mandate review` closure 完成之后，把 `01_mandate` 冻结成正式 `02_data_ready` 产物。

这里的 `data_ready` 不是静默跑数据，而是交互式冻结“后续研究共同依赖的数据研究底座”。

## Required Inputs

- `01_mandate/mandate.md`
- `01_mandate/research_scope.md`
- `01_mandate/time_split.json`
- `01_mandate/run_config.toml`
- `01_mandate/stage_completion_certificate.yaml`

## Required Outputs

- `aligned_bars/`
- `rolling_stats/`
- `pair_stats/`
- `benchmark_residual/`
- `topic_basket_state/`
- `qc_report.parquet`
- `dataset_manifest.json`
- `validation_report.md`
- `data_contract.md`
- `dedupe_rule.md`
- `universe_summary.md`
- `universe_exclusions.csv`
- `universe_exclusions.md`
- `data_ready_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `extraction_contract`
- `quality_semantics`
- `universe_admission`
- `shared_derived_layer`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 mandate 产物
- 可以冻结共享研究底座与共享派生层
- 不得产出 thesis-specific signal 或收益结论
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 data_ready？`
- 不得静默修改 mandate 冻结的时间边界和 universe 口径

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。

## Working Rules

1. 确认 `01_mandate/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `extraction_contract`
3. 再收敛并确认 `quality_semantics`
4. 再收敛并确认 `universe_admission`
5. 再收敛并确认 `shared_derived_layer`
6. 最后确认 `delivery_contract`
7. 输出一份 grouped data_ready summary
8. 只有用户最终批准后，才生成正式 `02_data_ready` artifacts
9. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
