---
name: qros-csf-backtest-ready-author
description: Use when reviewed csf_test_evidence outputs must be frozen into formal csf_backtest_ready artifacts through grouped interactive confirmation.
---

# CSF Backtest Ready Author

## Purpose

只在 `csf_test_evidence review` closure 完成之后，把 `05_csf_test_evidence` 冻结成正式 `06_csf_backtest_ready` 产物。

这里的 `csf_backtest_ready` 不是给因子再换一套解释，而是把 cross-sectional factor 路线后续必须复用的组合表达、风险覆盖和容量证据正式落盘。

QROS 仓库提供的是流程框架，不替用户的研究仓“代存”真实研究产物。agent 使用本 skill 时，必须在当前 research repo 里真实物化 `06_csf_backtest_ready` 需要交付的组合合同、引擎结果和容量证据，而不是把 placeholder 文件或只有合同语义的说明文档当作 csf_backtest_ready 完成。

## Runtime Stage Admission

开始本 stage-specific author 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage csf_backtest_ready --lane author`

若命令失败，必须停止；不得继续 authoring，不得补 artifact，不得绕过 `qros-research-session` 的 `current_stage`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## Required Inputs

- 已通过 review closure 的 `05_csf_test_evidence/author/formal/*`
- `05_csf_test_evidence/author/formal/csf_selected_variants_test.csv`
- `05_csf_test_evidence/author/formal/csf_test_gate_table.csv`
- `05_csf_test_evidence/author/formal/csf_test_contract.md`
- `01_mandate/author/formal/research_route.yaml`
- `contracts/artifacts/csf_backtest_ready_artifacts.yaml`

## Required Outputs

- `portfolio_contract.yaml`
- `portfolio_weight_panel.parquet`
- `rebalance_ledger.csv`
- `turnover_capacity_report.parquet`
- `cost_assumption_report.md`
- `portfolio_summary.parquet`
- `portfolio_return_series.parquet`
- `equity_curve.parquet`
- `portfolio_pnl_ledger.parquet`
- `asset_pnl_ledger.parquet`
- `risk_adjusted_metrics.parquet`
- `name_level_metrics.parquet`
- `drawdown_report.json`
- `target_strategy_compare.parquet`
- `csf_backtest_gate_table.csv`
- `return_accounting_provenance.yaml`
- `csf_backtest_contract.md`
- `csf_backtest_gate_decision.md`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `portfolio_contract`
- `execution_contract`
- `risk_contract`
- `diagnostic_contract`
- `delivery_contract`

这些 group 的 runtime-facing 字段以 `runtime/tools/csf_backtest_runtime.py` 的 draft skeleton 和 `docs/guides/stage-freeze-group-field-guide.md` 为准。skill 只解释确认顺序，不再维护 formal artifact 字段真值。

## Mandatory Discipline

- 只能消费已经通过 review closure 的 csf_test_evidence 产物
- 当前阶段只冻结组合规则与回测合同，不回写上游 factor 结论
- 必须显式使用 `factor_role`、`factor_structure`、`portfolio_expression` 和 `neutralization_policy` 的已冻结语义
- 必须在当前 research repo 里真实生成组合权重、引擎结果和容量证据
- 不得手写或自行扩展 formal artifact shape；formal artifact shape 以 `contracts/artifacts/csf_backtest_ready_artifacts.yaml` 为准
- 必须使用 runtime scaffold/build 物化 `06_csf_backtest_ready/author/formal/*`
- build 后必须运行 `qros-validate-stage --stage csf_backtest_ready`
- 进入 review 前必须通过 csf_backtest_ready semantic validator / deterministic preflight
- `portfolio_return_series.parquet`、`equity_curve.parquet`、`portfolio_pnl_ledger.parquet`、`asset_pnl_ledger.parquet`、`risk_adjusted_metrics.parquet` 是 formal hard contract；缺失、不可复算或与 formal return / PnL 序列不一致时不得进入 review
- 不得产出任何时序主线措辞、best_h、单资产命中率或 horizon 语义
- 必须先显式生成或刷新本 stage 的 lineage-local stage program，再执行 author build；QROS runtime 只负责校验和调用，不再后台静默生成默认 wrapper
- 该 stage program 必须是当前 lineage 在本 stage 里真实产生产物的程序，必须明确 formal artifacts 的生成路径、输入绑定和 replay 入口
- thin wrapper、framework builder shim、只转发共享 helper 的 skeleton 都不合法；`run_stage.py` 与关键 helper 不能只是把框架 builder 包一层
- 空目录、placeholder `parquet/csv/json/md`、只有说明文档都不能算正式完成
- 必须先回显 freeze draft；可以逐组确认，也可以一次展示全部 groups 后接受 `确认全部` 批量确认 groups
- 五组全部确认后，才允许最终 `是否按以上内容冻结 csf_backtest_ready？`
- 不得在 backtest 阶段重新选择 factor 或重估 train 尺子

- 若本阶段需要新增或修改代码，必须为真实产生产物的程序中的关键步骤、关键逻辑、阶段门禁、分支判断和易误解流程补充清晰、简短、面向维护者的中文注释；不要求逐行注释，也不要求回填历史代码。
- 语言规则统一遵守 `docs/guides/qros-authoring-language-discipline.md`，不要在本 skill 内再发明例外口径。

## Gate Discipline

### 组合表达必须显式
`portfolio_expression` 必须已经在上游冻结，并在本阶段被正确消费：
- `standalone_alpha`：
  - `long_short_market_neutral`
  - `long_only_rank`
  - `short_only_rank`
  - `benchmark_relative_long_only`
  - `group_relative_long_short`
- `regime_filter`：
  - `target_strategy_filter`
- `combo_filter`：
  - `target_strategy_filter`
  - `target_strategy_overlay`

### Artifact shape 由 contract 决定
`portfolio_contract.yaml`、`portfolio_weight_panel.parquet`、`csf_backtest_gate_table.csv`、`csf_backtest_gate_decision.md`、`run_manifest.json` 与所有 parquet columns 必须通过 `contracts/artifacts/csf_backtest_ready_artifacts.yaml` 校验。agent 不得因为 skill 文本、聊天上下文或 reviewer 偏好新增 formal artifact 字段。

### 路径级风险诊断必须可复算
`portfolio_return_series.parquet`、`equity_curve.parquet`、`portfolio_pnl_ledger.parquet`、`asset_pnl_ledger.parquet` 与 `risk_adjusted_metrics.parquet` 必须彼此可复算。365 天是 crypto 永续主口径，252 天是参考口径；Sharpe、Sortino、Calmar、profit factor 不新增 PASS 阈值，但缺失、不可复算或不一致会阻断 validation。

### 容量与成本必须可追溯
`turnover_capacity_report.parquet` 与 `cost_assumption_report.md` 中的成本假设、流动性代理和参与率边界必须可追溯至上游冻结口径。

### Formal Return Accounting 必须可追溯
必须产出 `return_accounting_provenance.yaml`，并让 `portfolio_summary.parquet` 与 `csf_backtest_gate_table.csv` 可追溯到该 provenance。

- Formal PnL 必须来自 `csf_data_ready` 的 tradable return / market price source，或来自明确 execution ledger。
- 不得使用 mom_ret 作为 formal PnL，也不得把 factor score、rank score、neutralized factor 或 signal/factor panel proxy return 写进 formal gate metrics。
- signal/factor panel proxy return 只能作为 diagnostic，不得进入 `portfolio_summary.parquet`、`csf_backtest_gate_table.csv` 或 review pass 口径。
- 缺少 tradable return source 时不得伪造 backtest；应停止普通推进并写出 blocking handoff，说明缺少真实可交易收益来源。

## Working Rules

1. 确认 `05_csf_test_evidence` 已有 review closure，且 formal artifacts 不是 placeholder
2. 先收敛并确认 `portfolio_contract`
3. 再收敛并确认 `execution_contract`
4. 再收敛并确认 `risk_contract`
5. 再收敛并确认 `diagnostic_contract`
6. 最后确认 `delivery_contract`
7. 明确当前 research repo 中由谁负责真实生成组合权重、rebalance ledger、容量证据和成本后 portfolio summary
8. 输出一份 grouped csf_backtest_ready summary
9. 只有用户最终批准后，才生成正式 `06_csf_backtest_ready` artifacts
10. 运行 `qros-validate-stage --stage csf_backtest_ready`
11. 运行 csf_backtest_ready semantic validator / deterministic preflight；validator/preflight 不通过，不得进入 `csf_backtest_ready` review
12. 为 machine-readable artifacts 补 `artifact_catalog.md` 与 `field_dictionary.md`
13. 若当前只能产出 skeleton 或 placeholder，必须明确判定为未完成，不得冒充 csf_backtest_ready 完成
