# CSF Backtest Ready SOP（横截面因子回测就绪阶段）

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-CSF-BACKTEST-READY-v1.0 |
| 日期 | 2026-03-30 |
| 状态 | Active |

---

## 0. 文档定位

本文档定义 `research_route = cross_sectional_factor` 时的 `06_csf_backtest_ready` 阶段。  
这一层把冻结后的因子分数映射成正式组合，并验证净成本后的经济可行性。

## 0.1 入口身份冻结约定

`factor_role`、`factor_structure`、`portfolio_expression`、`neutralization_policy` 是 `mandate` 冻结的研究身份字段，不在本阶段重新定义。  
若 `factor_role != standalone_alpha`，必须已经在 `mandate` 中冻结 `target_strategy_reference`；若 `neutralization_policy = group_neutral`，必须已经在 `mandate` 中冻结 `group_taxonomy_reference`。  
本阶段只冻结组合表达与映射，不改变研究身份。

---

## 1. 核心问题

**核心问题**：冻结后的因子分数映射成正式组合后，是否具备成本后的经济可行性。

**阶段职责**：
- 冻结组合表达
- 冻结权重映射
- 冻结成本和容量口径
- 冻结组合级可行性证据

---

## 2. 支持的组合表达

第一版正式支持以下组合表达，并要求与 `factor_role` 匹配：

- `standalone_alpha`
  - `long_short_market_neutral`
  - `long_only_rank`
  - `short_only_rank`
  - `benchmark_relative_long_only`
  - `group_relative_long_short`
- `regime_filter`
  - `target_strategy_filter`
- `combo_filter`
  - `target_strategy_filter`
  - `target_strategy_overlay`

---

## 3. 必备输出

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

条件性输出：
- `gated_portfolio_summary.parquet`
- `ungated_portfolio_summary.parquet`

---

## 3.1 路径级风险诊断 hard contract

`portfolio_return_series.parquet`、`equity_curve.parquet`、`portfolio_pnl_ledger.parquet`、`asset_pnl_ledger.parquet` 与 `risk_adjusted_metrics.parquet` 是本阶段 formal hard contract。它们必须存在、非空，并能由 deterministic preflight 互相复算：

- `equity_curve.parquet` 必须能由 `portfolio_return_series.parquet` 的 gross / net return 从初始净值 1.0 复算。
- `portfolio_pnl_ledger.parquet` 必须能与 return series 的收益、成本和 `capital_base` 对齐。
- `asset_pnl_ledger.parquet` 必须能聚合回 portfolio PnL，并与冻结的 `portfolio_expression` 暴露规则一致。
- `risk_adjusted_metrics.parquet` 中 Sharpe、Sortino、Calmar、profit factor 必须能由 formal return / PnL 序列复算。

365 天是 crypto 永续主口径；252 天是传统交易日参考口径。Sharpe、Sortino、Calmar、profit factor 不新增 PASS 阈值；它们可以表现很差，但缺失、不可复算或与原始序列不一致会阻断 stage validation。这里的“不新增 PASS 阈值”只表示不因为 Sharpe / Calmar / profit factor 数值低而机器失败，不表示可以缺少这些产物。

---

## 4. Formal Gate

必须全部满足：

- 只消费 `05_csf_test_evidence` 冻结通过的 variants
- 组合规则 machine-readable 冻结
- 成本后结果仍具经济意义
- 换手、容量、参与率分析完整
- 组合结果不是极少数 name 或日期单独支撑
- 组合表达与 `mandate` 冻结一致
- `return_accounting_provenance.yaml` 已证明 formal PnL 来自 `csf_data_ready` 的 tradable return / market price source 或 execution ledger

必须失败任一：

- backtest 内重新挑选 variant
- 改变 long/short cut 或权重规则却不回退
- 只报 gross，不报 net after cost
- 没有 name-level concentration 诊断
- 容量分析缺失
- 结果只靠单一极端窗口或单一资产支撑
- `mom_ret`、signal/factor score、rank score、neutralized factor 或其他 proxy PnL 进入 `portfolio_summary.parquet`、`csf_backtest_gate_table.csv` 或 review pass

---

## 5. 禁止事项

- 不得在 backtest 重新定义因子
- 不得把组合表达当作 signal_ready 的一部分
- 不得在这里解释机制，只能验证组合可行性
- 不得把未冻结的组合规则带入净值计算
- proxy PnL 只能放在 diagnostic 中，不能作为 formal backtest metrics
