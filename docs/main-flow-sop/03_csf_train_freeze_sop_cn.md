# CSF Train Freeze SOP

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-CSF-TRAIN-FREEZE-v1.0 |
| 日期 | 2026-03-30 |
| 状态 | Active |

---

## 0. 文档定位

本文档定义 `research_route = cross_sectional_factor` 时的 `03_csf_train_freeze` 阶段。  
这一层只负责冻结截面尺子，不宣布胜利，不挑最终赢家。

## 0.1 入口身份冻结约定

`factor_role`、`factor_structure`、`portfolio_expression`、`neutralization_policy` 是 `mandate` 冻结的研究身份字段，不在本阶段重新定义。  
若 `factor_role != standalone_alpha`，必须已经在 `mandate` 中冻结 `target_strategy_reference`；若 `neutralization_policy = group_neutral`，必须已经在 `mandate` 中冻结 `group_taxonomy_reference`。  
本阶段只冻结 train 尺子与 admissible variants，不改变研究身份和路线归属。
一旦 `02_csf_signal_ready` 已经冻结 `factor expression`，`fragility_score_transform`、`raw_factor_fields`、`derived_factor_fields`、`score_combination_formula` 就不再属于 train 可调轴；若想改变这些内容，必须回到 `02_csf_signal_ready` 重开信号合同。

---

## 1. 核心问题

**核心问题**：截面因子的预处理、标准化、中性化、分组和再平衡口径如何在 train 内冻结。

**阶段职责**：
- 冻结 preprocess
- 冻结 neutralization
- 冻结 bucket / quantile schema
- 冻结 rebalance 口径
- 冻结 admissible variants

---

## 2. 必须完成

1. 冻结 `winsorize_policy`、`standardize_policy`、`missing_fill_policy`、`coverage_floor_rule`。
2. 冻结 `neutralization_policy`、`beta_estimation_window`、`group_taxonomy_version`。
3. 冻结 `ranking_scope`、`bucket_schema`、`quantile_count`、`tie_break_rule`、`min_names_per_bucket`。
4. 冻结 `rebalance_frequency`、`signal_lag_rule`、`holding_period_rule`、`overlap_policy`。
5. 冻结 `min_cross_section_size`、`min_effective_coverage`、`asset_drop_rule`、`date_drop_rule`。
6. 明确写清 `frozen_signal_contract_reference`、`train_governable_axes`、`non_governable_axes_after_signal` 和 `non_governable_axis_reject_rule`。
7. 记账所有 admissible variants 和 reject variants。

---

## 3. 必备输出

- `csf_train_freeze.yaml`
- `train_factor_quality.parquet`
- `train_variant_ledger.csv`
- `train_variant_rejects.csv`
- `train_bucket_diagnostics.parquet`
- `csf_train_contract.md`
- `artifact_catalog.md`
- `field_dictionary.md`

条件性输出：
- `train_neutralization_diagnostics.parquet`

---

## 4. Formal Gate

必须全部满足：

- preprocess、standardize、neutralize、bucket、rebalance、eligibility 全部冻结
- signal-ready 已冻结的表达轴不再被当作 train 可调轴
- 所有 train variant 都有身份记录
- reject 不是静默丢弃，而是显式记账
- downstream test 只能复用 frozen train rules
- neutralization 如存在，必须有独立合同和诊断

必须失败任一：

- 根据 test/backtest 结果回写 train 口径
- 只有保留者，没有 reject ledger
- quantile / bucket 规则未冻结
- 已冻结的 signal expression 轴被重新当作 train 搜索轴
- neutralization 存在但没有独立合同
- rebalance / lag / overlap 口径未冻结
- 在 train 内直接用收益最大化选 final winner

---

## 5. 禁止事项

- 不得把 train 变成隐形 backtest
- 不得在这一层宣布最终 champion
- 不得把 test 里才知道的 cutoff 写回 train
- 不得让 `filter` 语义在 train 阶段偷偷改变研究身份
