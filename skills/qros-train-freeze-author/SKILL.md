---
name: qros-train-freeze-author
description: Use when reviewed signal_ready outputs must be frozen into formal train-freeze artifacts through grouped interactive confirmation.
---

# Train Freeze Author

## Purpose

只在 `signal_ready review` closure 完成之后，把 `03_signal_ready` 冻结成正式 `04_train_freeze` 产物。

这里的 `train_freeze` 不是在 QROS 框架仓里写一份训练合同示意，而是要在当前 research repo 中把后续 `test_evidence` 必须复用的 train 冻结结果正式落盘。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `04_train_freeze` 需要交付的 thresholds、quality 证据和参数台账，而不是把 placeholder 文件或只有合同语义的说明文档当作 train_freeze 完成。

## Required Inputs

- `03_signal_ready/param_manifest.csv`
- `03_signal_ready/params/`
- `03_signal_ready/signal_coverage.csv`
- `03_signal_ready/signal_fields_contract.md`
- `03_signal_ready/stage_completion_certificate.yaml`
- `01_mandate/time_split.json`

## Required Outputs

- `train_thresholds.json`
- `train_quality.parquet`
- `train_param_ledger.csv`
- `train_rejects.csv`
- `train_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `window_contract`
- `threshold_contract`
- `quality_filters`
- `param_governance`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 signal_ready 产物
- 当前阶段只冻结 train 合同，不替策略宣布“赢家”
- 参数 ledger 必须完整保留，reject ledger 必须单独落盘
- 必须在当前研究仓真实生成训练窗估计得到的 thresholds、quality 证据、kept or rejected ledger
- placeholder `parquet/csv/json/md`、空目录或只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 train_freeze？`
- 不得借用 test/backtest 结果回写 train 尺子

## Working Rules

1. 确认 `03_signal_ready/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `window_contract`
3. 再收敛并确认 `threshold_contract`
4. 再收敛并确认 `quality_filters`
5. 再收敛并确认 `param_governance`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 thresholds、quality 证据、param ledger 和 reject ledger
8. 输出一份 grouped train_freeze summary
9. 只有用户最终批准后，才生成正式 `04_train_freeze` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 train_freeze 完成
