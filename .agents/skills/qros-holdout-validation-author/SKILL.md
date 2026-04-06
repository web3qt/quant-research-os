---
name: qros-holdout-validation-author
description: Use when reviewed backtest_ready outputs must be frozen into formal holdout_validation artifacts through grouped interactive confirmation.
---

# Holdout Validation Author

## Purpose

只在 `backtest_ready review` closure 完成之后，把 `06_backtest` 冻结成正式 `07_holdout` 产物。

这里的 `holdout_validation` 不是让策略 agent 借机重新设计规则，而是把最终未参与设计的窗口验证合同正式落盘，确保后续只能解释结果，不能回写参数。

## Required Inputs

- `06_backtest/backtest_frozen_config.json`
- `06_backtest/selected_strategy_combo.json`
- `06_backtest/stage_completion_certificate.yaml`
- `01_mandate/time_split.json`

## Required Outputs

- `holdout_run_manifest.json`
- `holdout_backtest_compare.csv`
- `window_results/`
- `holdout_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `window_contract`
- `reuse_contract`
- `drift_audit`
- `failure_governance`
- `delivery_contract`

## Mandatory Discipline

- 只能复用已经通过 review closure 的 backtest 冻结方案
- 不得在 holdout 阶段改参数、改 `best_h`、改 symbol 白名单、改交易规则
- 必须同时保留单窗口和合并窗口结果口径
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 holdout_validation？`
- `holdout` 只能产生验证结论、重跑边界和 child lineage 触发条件，不能回写主线规则

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。

## Working Rules

1. 确认 `06_backtest/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `window_contract`
3. 再收敛并确认 `reuse_contract`
4. 再收敛并确认 `drift_audit`
5. 再收敛并确认 `failure_governance`
6. 最后确认 `delivery_contract`
7. 输出一份 grouped holdout_validation summary
8. 只有用户最终批准后，才生成正式 `07_holdout` artifacts
9. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
