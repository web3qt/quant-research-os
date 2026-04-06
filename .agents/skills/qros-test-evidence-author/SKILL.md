---
name: qros-test-evidence-author
description: Use when reviewed train_freeze outputs must be frozen into formal test_evidence artifacts through grouped interactive confirmation.
---

# Test Evidence Author

## Purpose

只在 `train_freeze review` closure 完成之后，把 `04_train_freeze` 冻结成正式 `05_test_evidence` 产物。

这里的 `test_evidence` 不是替策略跑真实统计检验，而是把后续 `backtest_ready` 必须复用的 test 合同正式落盘。

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
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 test_evidence？`
- 不得在 test 窗里重估 train thresholds、whitelist 或 best_h

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。

## Working Rules

1. 确认 `04_train_freeze/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `window_contract`
3. 再收敛并确认 `formal_gate_contract`
4. 再收敛并确认 `admissibility_contract`
5. 再收敛并确认 `audit_contract`
6. 最后确认 `delivery_contract`
7. 输出一份 grouped test_evidence summary
8. 只有用户最终批准后，才生成正式 `05_test_evidence` artifacts
9. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
