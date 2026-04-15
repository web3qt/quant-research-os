# CSF Test Evidence SOP

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-CSF-TEST-EVIDENCE-v1.0 |
| 日期 | 2026-03-30 |
| 状态 | Active |

---

## 0. 文档定位

本文档定义 `research_route = cross_sectional_factor` 时的 `04_csf_test_evidence` 阶段。  
这一层要把 `factor_role` 分成 `standalone_alpha` 和 `regime_filter / combo_filter` 两套证据语义。

## 0.1 入口身份冻结约定

`factor_role`、`factor_structure`、`portfolio_expression`、`neutralization_policy` 是 `mandate` 冻结的研究身份字段，不在本阶段重新定义。  
若 `factor_role != standalone_alpha`，必须已经在 `mandate` 中冻结 `target_strategy_reference`；若 `neutralization_policy = group_neutral`，必须已经在 `mandate` 中冻结 `group_taxonomy_reference`。  
本阶段只验证证据，不允许把身份字段改写成新的研究路线。

---

## 1. 核心问题

**核心问题**：冻结后的截面排序能力，或截面 filter / combo 条件改善能力，是否在独立样本仍然成立。

**阶段职责**：
- 复用 train 冻结规则
- 计算独立样本证据
- 冻结 test white list / admissible set
- 保留全量 test ledger

---

## 2. `standalone_alpha` 证据

主证据：
- `Rank IC`
- `ICIR`
- bucket / quantile return spread
- monotonicity
- breadth
- subperiod stability

必备输出：
- `rank_ic_timeseries.parquet`
- `rank_ic_summary.json`
- `bucket_returns.parquet`
- `monotonicity_report.json`
- `breadth_coverage_report.parquet`
- `subperiod_stability_report.json`
- `csf_test_gate_table.csv`
- `csf_selected_variants_test.csv`
- `csf_test_contract.md`

---

## 3. `regime_filter / combo_filter` 证据

主证据：
- gated vs ungated 改善
- drawdown 改善
- tail risk 改善
- 稳定性改善
- 覆盖率不过低

必备输出：
- `filter_condition_panel.parquet`
- `target_strategy_condition_compare.parquet`
- `gated_vs_ungated_summary.json`
- `drawdown_compare.json`
- `tail_risk_compare.json`
- `coverage_participation_report.parquet`
- `csf_test_gate_table.csv`
- `csf_selected_variants_test.csv`
- `csf_test_contract.md`

---

## 4. Formal Gate

### `standalone_alpha`

必须全部满足：

- 只复用 `03_csf_train_freeze` 的 frozen rules
- `Rank IC` 方向与 `factor_direction` 一致
- 至少一类主要排序证据成立：`Rank IC` 或 bucket spread
- 单调性未完全崩塌
- breadth / coverage 没有低到只靠极少数日期支撑
- 子窗口未明显翻向

### `regime_filter / combo_filter`

必须全部满足：

- `target_strategy_reference` 与上游冻结一致
- filter / combo 的作用位置冻结且一致
- 至少改善一类主要目标分布
- 覆盖率不能低到近乎停摆
- 改善不能只来自单一极端日期

### Shared Failure Rules

必须失败任一：

- test 内重估 train 尺子
- 新增未冻结 variant
- 看 backtest 后回写 `selected_variants_test`
- 只保留通过者，不保留全量 variant ledger
- 搜索量较大却不做 multiple testing 校正

---

## 5. 禁止事项

- 不得把 filter 语义当成 standalone alpha 语义
- 不得把 standalone alpha 的 IC 替代组合改善证据
- 不得让 test 变成选冠军现场
- 不得在 test 中重估任何 train 尺子
