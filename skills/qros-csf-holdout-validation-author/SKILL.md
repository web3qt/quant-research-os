---
name: qros-csf-holdout-validation-author
description: Use when reviewed csf_backtest_ready outputs must be frozen into formal csf_holdout_validation artifacts through grouped interactive confirmation.
---

# CSF Holdout Validation Author

## Purpose

只在 `csf_backtest_ready review` closure 完成之后，把 `06_csf_backtest_ready` 冻结成正式 `07_csf_holdout_validation` 产物。

这里的 `csf_holdout_validation` 不是重新设计规则，而是把最终未参与设计的窗口验证合同正式落盘，确保后续只能解释结果，不能回写 factor 或组合参数。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `07_csf_holdout_validation` 需要交付的单窗口与合并窗口结果、对比结果和验证证据，而不是把 placeholder 文件或只有合同语义的说明文档当作 csf_holdout_validation 完成。

## Required Inputs

- `06_csf_backtest_ready/frozen_portfolio_spec.json`
- `06_csf_backtest_ready/strategy_combo_ledger.csv`
- `06_csf_backtest_ready/stage_completion_certificate.yaml`
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

- 只能复用已经通过 review closure 的 csf_backtest_ready 冻结方案
- 不得在 holdout 阶段改参数、改 factor 选择、改组合规则或改任何已冻结语义
- 必须同时保留单窗口和合并窗口结果口径
- 必须在当前 research repo 里真实生成单窗口、合并窗口和对比结果，而不是只落合同说明
- 空目录、placeholder `parquet/csv/json/md`、只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_holdout_validation？`
- holdout 只能产生验证结论、漂移解释和 child lineage 触发条件，不能回写主线规则

## Gate Discipline

### Rolling OOS 一致性低必须有显式解释
若 `holdout_backtest_compare.csv` 中 rolling OOS 一致性得分 < 0.6，不得静默通过：
- 必须在 `drift_audit` 组中提供显式解释
- 解释必须对应到具体时间段和可识别原因
- 若无法给出可识别解释，holdout gate 最高为 `CONDITIONAL PASS`

### 方向翻转定义与处置
在 `drift_audit` 组冻结前，必须预先定义"方向翻转"的判断标准：
- 何为方向翻转：holdout 期间信号方向与 backtest 期间一致性的偏差阈值
- 翻转发生时的处置路径：记录为 drift 事件、触发 child lineage 还是进入人工审核
- 不允许事后根据翻转是否有利来决定处置方式

### 严禁 Holdout 与 Backtest 结果合并
`holdout_backtest_compare.csv` 只能用于对比，不得将 holdout 结果与 backtest 结果合并成单一绩效曲线。

## Working Rules

1. 确认 `06_csf_backtest_ready/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `window_contract`
3. 再收敛并确认 `reuse_contract`
4. 再收敛并确认 `drift_audit`
5. 再收敛并确认 `failure_governance`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成单窗口结果、合并窗口结果、compare 输出和验证证据
8. 输出一份 grouped csf_holdout_validation summary
9. 只有用户最终批准后，才生成正式 `07_csf_holdout_validation` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_holdout_validation 完成
