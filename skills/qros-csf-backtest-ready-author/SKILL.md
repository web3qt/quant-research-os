---
name: qros-csf-backtest-ready-author
description: Use when reviewed csf_test_evidence outputs must be frozen into formal csf_backtest_ready artifacts through grouped interactive confirmation.
---

# CSF Backtest Ready Author

## Purpose

只在 `csf_test_evidence review` closure 完成之后，把 `05_csf_test_evidence` 冻结成正式 `06_csf_backtest_ready` 产物。

这里的 `csf_backtest_ready` 不是给因子再换一套解释，而是把 cross-sectional factor 路线后续必须复用的组合表达、风险覆盖和容量证据正式落盘。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `06_csf_backtest_ready` 需要交付的组合合同、引擎结果和容量证据，而不是把 placeholder 文件或只有合同语义的说明文档当作 csf_backtest_ready 完成。

## Required Inputs

- `05_csf_test_evidence/selected_factor_spec.json`
- `05_csf_test_evidence/factor_selection.csv`
- `05_csf_test_evidence/test_gate_decision.md`
- `05_csf_test_evidence/stage_completion_certificate.yaml`

## Required Outputs

- `frozen_portfolio_spec.json`
- `portfolio_weight_panel.parquet`
- `portfolio_curve.parquet`
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

- 只能消费已经通过 review closure 的 csf_test_evidence 产物
- 当前阶段只冻结组合规则与回测合同，不回写上游 factor 结论
- 必须显式使用 `factor_role`、`factor_structure`、`portfolio_expression` 和 `neutralization_policy` 的已冻结语义
- 必须在当前 research repo 里真实生成组合权重、引擎结果和容量证据
- 不得产出任何时序主线措辞、best_h、单资产命中率或 horizon 语义
- 空目录、placeholder `parquet/csv/json/md`、只有说明文档都不能算正式完成
- 每一组都要先回显 freeze draft，再确认该组
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_backtest_ready？`
- 不得在 backtest 阶段重新选择 factor 或重估 train 尺子

## Gate Discipline

### 组合表达必须显式
`portfolio_expression` 必须已经在上游冻结，并在本阶段被正确消费：
- `long_short_market_neutral`
- `long_only_rank`

### 组合台账必须有理由
`strategy_combo_ledger.csv` 中每条组合配置记录必须包含非空的 `selection_rationale` 字段。

### 容量与成本必须可追溯
`capacity_review.md` 中的成本假设、流动性代理和参与率边界必须可追溯至上游冻结口径。

## Working Rules

1. 确认 `05_csf_test_evidence/stage_completion_certificate.yaml` 已存在
2. 先收敛并确认 `execution_policy`
3. 再收敛并确认 `portfolio_policy`
4. 再收敛并确认 `risk_overlay`
5. 再收敛并确认 `engine_contract`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成组合权重、引擎结果、combo ledger 和容量证据
8. 输出一份 grouped csf_backtest_ready summary
9. 只有用户最终批准后，才生成正式 `06_csf_backtest_ready` artifacts
10. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
11. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_backtest_ready 完成
