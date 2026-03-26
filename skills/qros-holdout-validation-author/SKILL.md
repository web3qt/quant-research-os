---
name: qros-holdout-validation-author
description: Use when reviewed backtest_ready outputs must be frozen into formal holdout_validation artifacts through grouped interactive confirmation.
---

# Holdout Validation Author

## Purpose

只在 `backtest_ready review` closure 完成之后，把 `06_backtest` 冻结成正式 `07_holdout` 产物。

这里的 `holdout_validation` 不是让策略 agent 借机重新设计规则，而是把最终未参与设计的窗口验证合同正式落盘，确保后续只能解释结果，不能回写参数。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `07_holdout` 需要交付的单窗口与合并窗口结果、对比结果和验证证据，而不是把 placeholder 文件或只有合同语义的说明文档当作 holdout_validation 完成。

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
- 必须在当前研究仓真实生成单窗口、合并窗口和对比结果，而不是只落合同说明
- placeholder `parquet/csv/json/md`、空目录或只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 holdout_validation？`
- `holdout` 只能产生验证结论、重跑边界和 child lineage 触发条件，不能回写主线规则

## Working Rules

1. 确认 `06_backtest/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `window_contract`
3. 再收敛并确认 `reuse_contract`
4. 再收敛并确认 `drift_audit`
5. 再收敛并确认 `failure_governance`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成单窗口结果、合并窗口结果、compare 输出和验证证据
8. 输出一份 grouped holdout_validation summary
9. 只有用户最终批准后，才生成正式 `07_holdout` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 holdout_validation 完成
