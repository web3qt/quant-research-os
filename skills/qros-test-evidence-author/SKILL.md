---
name: qros-test-evidence-author
description: Use when reviewed train_freeze outputs must be frozen into formal test_evidence artifacts through grouped interactive confirmation.
---

# Test Evidence Author

## Purpose

只在 `train_freeze review` closure 完成之后，把 `04_train_freeze` 冻结成正式 `05_test_evidence` 产物。

这里的 `test_evidence` 不是在 QROS 框架仓里写一份 test 合同示意，而是要在当前 research repo 中把后续 `backtest_ready` 必须复用的 test 统计证据正式落盘。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `05_test_evidence` 需要交付的 test 统计结果、admissibility 结果和冻结对象，而不是把 placeholder 文件或只有合同语义的说明文档当作 test_evidence 完成。

## Required Inputs

- `04_train_freeze/train_thresholds.json`
- `04_train_freeze/train_param_ledger.csv`
- `03_signal_ready/param_manifest.csv`
- `02_data_ready/aligned_bars/`
- `01_mandate/time_split.json`
- `04_train_freeze/stage_completion_certificate.yaml`

## Required Outputs

- `report_by_h.parquet`
- `symbol_summary.parquet`
- `admissibility_report.parquet`
- `test_gate_table.csv`
- `crowding_review.md`
- `selected_symbols_test.csv`
- `selected_symbols_test.parquet`
- `frozen_spec.json`
- `test_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `window_contract`
- `formal_gate_contract`
- `admissibility_contract`
- `audit_contract`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 train_freeze 产物
- 当前阶段只冻结 test 合同，不替策略宣布交易层胜利
- formal gate 与 audit gate 必须显式分开
- 必须在当前研究仓真实生成独立测试窗上的统计证据、admissibility 结果和冻结 whitelist/best_h
- placeholder `parquet/csv/json/md`、空目录或只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 test_evidence？`
- 不得在 test 窗里重估 train thresholds、whitelist 或 best_h

## Working Rules

1. 确认 `04_train_freeze/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `window_contract`
3. 再收敛并确认 `formal_gate_contract`
4. 再收敛并确认 `admissibility_contract`
5. 再收敛并确认 `audit_contract`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成 test 统计证据、admissibility 结果、selected symbols 和 frozen spec
8. 输出一份 grouped test_evidence summary
9. 只有用户最终批准后，才生成正式 `05_test_evidence` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 test_evidence 完成
