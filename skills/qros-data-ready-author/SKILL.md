---
name: qros-data-ready-author
description: Use when a reviewed mandate must be frozen into formal data_ready artifacts through grouped interactive confirmation.
---

# Data Ready Author

## Purpose

只在 `mandate review` closure 完成之后，把 `01_mandate` 冻结成正式 `02_data_ready` 产物。

这里的 `data_ready` 不是静默跑数据，而是交互式冻结“后续研究共同依赖的数据研究底座”。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `02_data_ready` 需要交付的共享数据层，而不是把空目录、placeholder 文件或只有合同语义的说明文档当作 data_ready 完成。

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
- 必须在当前研究仓真实生成可供下游消费的 `aligned_bars/`、共享缓存和相关证据
- 空目录、placeholder `parquet/csv/md`、只有口头或文档语义说明的产物都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 data_ready？`
- 不得静默修改 mandate 冻结的时间边界和 universe 口径

## Working Rules

1. 确认 `01_mandate/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `extraction_contract`
3. 再收敛并确认 `quality_semantics`
4. 再收敛并确认 `universe_admission`
5. 再收敛并确认 `shared_derived_layer`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 `aligned_bars/`、rolling 缓存、coverage/QC 证据和 shared derived outputs
8. 输出一份 grouped data_ready summary
9. 只有用户最终批准后，才生成正式 `02_data_ready` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 data_ready 完成
