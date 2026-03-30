# CSF Backtest Ready SOP

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-CSF-BACKTEST-READY-v1.0 |
| 日期 | 2026-03-30 |
| 状态 | Active |

---

## 0. 文档定位

本文档定义 `research_route = cross_sectional_factor` 时的 `05_csf_backtest_ready` 阶段。  
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

第一版只正式支持：

- `long_short_market_neutral`
- `long_only_rank`

---

## 3. 必备输出

- `portfolio_contract.yaml`
- `portfolio_weight_panel.parquet`
- `rebalance_ledger.csv`
- `turnover_capacity_report.parquet`
- `cost_assumption_report.md`
- `engine_compare.csv`
- `portfolio_summary.parquet`
- `name_level_metrics.parquet`
- `drawdown_report.json`
- `csf_backtest_gate_table.csv`
- `csf_backtest_contract.md`
- `artifact_catalog.md`
- `field_dictionary.md`

条件性输出：
- `target_strategy_compare.parquet`
- `gated_portfolio_summary.parquet`
- `ungated_portfolio_summary.parquet`

---

## 4. Formal Gate

必须全部满足：

- 只消费 `04_csf_test_evidence` 冻结通过的 variants
- 组合规则 machine-readable 冻结
- 成本后结果仍具经济意义
- 换手、容量、参与率分析完整
- 组合结果不是极少数 name 或日期单独支撑
- 组合表达与 `mandate` 冻结一致

必须失败任一：

- backtest 内重新挑选 variant
- 改变 long/short cut 或权重规则却不回退
- 只报 gross，不报 net after cost
- 没有 name-level concentration 诊断
- 容量分析缺失
- 结果只靠单一极端窗口或单一资产支撑

---

## 5. 禁止事项

- 不得在 backtest 重新定义因子
- 不得把组合表达当作 signal_ready 的一部分
- 不得在这里解释机制，只能验证组合可行性
- 不得把未冻结的组合规则带入净值计算
