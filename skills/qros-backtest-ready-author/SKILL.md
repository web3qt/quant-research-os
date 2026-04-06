---
name: qros-backtest-ready-author
description: Use when reviewed test_evidence outputs must be frozen into formal backtest_ready artifacts through grouped interactive confirmation.
---

# Backtest Ready Author

## Purpose

只在 `test_evidence review` closure 完成之后，把 `05_test_evidence` 冻结成正式 `06_backtest` 产物。

这里的 `backtest_ready` 不是在 QROS 框架仓里写一份回测合同示意，而是要在当前 research repo 中把后续 `holdout_validation` 必须复用的双引擎正式回测结果和交易合同落盘。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `06_backtest` 需要交付的双引擎回测结果、组合台账和容量证据，而不是把 placeholder 文件或只有合同语义的说明文档当作 backtest_ready 完成。

## Required Inputs

- `05_test_evidence/frozen_spec.json`
- `05_test_evidence/selected_symbols_test.csv`
- `05_test_evidence/stage_completion_certificate.yaml`

## Required Outputs

- `engine_compare.csv`
- `vectorbt/`
- `backtrader/`
- `strategy_combo_ledger.csv`
- `capacity_review.md`
- `backtest_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `execution_policy`
- `portfolio_policy`
- `risk_overlay`
- `engine_contract`
- `delivery_contract`

## Mandatory Discipline

- 只能消费已经通过 review closure 的 test_evidence 产物
- 当前阶段只冻结交易规则与回测合同，不回写上游 signal/train/test 结论
- 必须保留双引擎与策略组合 ledger 的正式口径
- 必须在当前研究仓真实生成 vectorbt 与 backtrader 两套回测结果、engine compare、组合台账和 capacity 证据
- placeholder `parquet/csv/json/md`、空目录或只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 backtest_ready？`
- 不得在 backtest 阶段重新选币或重估 best_h

- 若本阶段需要新增或修改代码，必须为关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。

## Gate Discipline

### 双引擎语义冲突解决定义
`engine_compare.csv` 中出现双引擎显著分歧时，必须有明确的解决规则：
- 必须在 `engine_contract` 冻结时预先定义：何为"显著分歧"（如 Sharpe 差 > X、最大回撤差 > Y）
- 显著分歧出现时的处置流程（以哪个引擎为准，还是进入人工审核）
- 不允许事后根据哪个引擎结果更好来决定采用哪套

### 成本与容量可解释性要求
`capacity_review.md` 中的每条容量结论必须可追溯至具体数据：
- 成本假设必须写明来源（参考数据、历史 fill rate、mandate 中的参与率边界）
- 容量估算必须基于 `01_mandate/time_split.json` 中记录的流动性代理变量和参与率边界
- 禁止填写无数据支撑的容量数字（如"估计可容纳 100万"无依据）
- 容量结论需与 mandate 中的 `crowding distinctiveness review` 基准保持一致

### 组合台账 combo_ledger 必须有理由
`strategy_combo_ledger.csv` 中每条组合配置记录必须包含非空的 `selection_rationale` 字段：
- 说明该组合配置的选择依据（信号多样性、风险分散、mandate 约束等）
- 禁止以"回测结果好"为单一理由选择组合配置
- 若有多个备选组合，必须记录未选择原因

### 异常表现必须触发溯源核查
若 backtest 结果出现以下任一异常表现，必须在宣布完成前完成溯源核查：
- Sharpe 显著高于 test_evidence 阶段的统计结论（如 test IC 均值仅 0.02，backtest Sharpe 却达到 3.0）
- 最大回撤极低但换手率极高（成本假设可能失真）
- 双引擎结果高度一致但与 test 窗统计差异极大

溯源核查结论必须写入 `backtest_gate_decision.md`；无法解释的异常不得通过 formal gate。

## Working Rules

1. 确认 `05_test_evidence/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `execution_policy`
3. 再收敛并确认 `portfolio_policy`；确认 combo_ledger 每条记录有 selection_rationale
4. 再收敛并确认 `risk_overlay`
5. 再收敛并确认 `engine_contract`；确认双引擎语义冲突解决规则已预先定义
6. 最后确认 `delivery_contract`；确认 capacity_review 成本假设可追溯，异常表现已溯源
7. 明确当前 research repo 中由谁负责真实生成双引擎回测结果、engine compare、combo ledger 和 capacity evidence
8. 输出一份 grouped backtest_ready summary
9. 只有用户最终批准后，才生成正式 `06_backtest` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 backtest_ready 完成
