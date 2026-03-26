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

## Working Rules

1. 确认 `05_test_evidence/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `execution_policy`
3. 再收敛并确认 `portfolio_policy`
4. 再收敛并确认 `risk_overlay`
5. 再收敛并确认 `engine_contract`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成双引擎回测结果、engine compare、combo ledger 和 capacity evidence
8. 输出一份 grouped backtest_ready summary
9. 只有用户最终批准后，才生成正式 `06_backtest` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 backtest_ready 完成
