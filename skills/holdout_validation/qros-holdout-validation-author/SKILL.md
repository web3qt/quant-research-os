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

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。
- 对 machine-readable 字段名、文件名、枚举值、命令、schema key 和上下游契约引用，保持英文或既有约定，不得为了中文化破坏契约。
- 对 hypothesis、counter-hypothesis、why、risk、evidence、uncertainty、kill reason、summary、rationale 等解释性内容，默认先判断是否适合中文；适合则优先用中文表达。
- 只有在英文表达更精确、需要与固定术语或上下游契约严格对齐、或用户明确要求英文时，才保留英文。

## Gate Discipline

### Rolling OOS 一致性低必须有显式解释
若 `holdout_backtest_compare.csv` 中 rolling OOS 一致性得分 < 0.6，不得静默通过：
- 必须在 `drift_audit` 组中提供显式解释（市场制度变化、样本量不足、特定时段异常等）
- 解释必须对应到具体的时间段和可识别原因，不接受"市场变了"等模糊说法
- 若无法给出可识别解释，holdout gate 最高为 `CONDITIONAL PASS`，且必须在 `holdout_gate_decision.md` 中记录

### 方向翻转定义与处置
在 `drift_audit` 组冻结前，必须预先定义"方向翻转"的判断标准：
- 何为方向翻转：holdout 期间信号方向（多/空）与 backtest 期间一致性的偏差阈值
- 翻转发生时的处置路径：记录为 drift 事件、触发 child lineage 还是进入人工审核
- 不允许事后根据翻转是否有利来决定处置方式

### 严禁 Holdout 与 Backtest 结果合并
`holdout_backtest_compare.csv` 只能用于**对比**，不得将 holdout 结果与 backtest 结果合并成单一绩效曲线：
- holdout 窗口必须在 `holdout_run_manifest.json` 中独立标记，不得与 train/test/backtest 窗口混合
- 任何将 holdout Sharpe 与 backtest Sharpe 加权平均或合并汇报的行为必须触发 **CHILD LINEAGE**
- `window_results/` 中每个子目录必须有独立的窗口标识符，不得复用 backtest 的命名

### 严禁在 Holdout 阶段修改规则
以下修改必须触发 **CHILD LINEAGE**，不得在 holdout 阶段发生：
- 修改 `best_h`
- 修改 symbol 白名单（`selected_symbols`）
- 修改任何 `train_thresholds.json` 中的阈值
- 修改交易规则（`execution_policy`、`portfolio_policy`、`risk_overlay`）

## Working Rules

1. 确认 `06_backtest/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `window_contract`；确认 holdout 窗口与 backtest 窗口完全隔离，无重叠
3. 再收敛并确认 `reuse_contract`；确认参数、best_h、symbol 白名单完全复用，无任何修改
4. 再收敛并确认 `drift_audit`；定义方向翻转判断标准和 rolling OOS 低一致性的解释要求
5. 再收敛并确认 `failure_governance`；确认 child lineage 触发条件已写清
6. 最后确认 `delivery_contract`；确认 holdout 结果未与 backtest 结果合并
7. 明确当前 research repo 中由谁负责真实生成单窗口结果、合并窗口结果、compare 输出和验证证据
8. 输出一份 grouped holdout_validation summary
9. 只有用户最终批准后，才生成正式 `07_holdout` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 holdout_validation 完成
