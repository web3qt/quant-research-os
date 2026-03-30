# CSF Signal Ready SOP

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-CSF-SIGNAL-READY-v1.0 |
| 日期 | 2026-03-30 |
| 状态 | Active |

---

## 0. 文档定位

本文档定义 `research_route = cross_sectional_factor` 时的 `02_csf_signal_ready` 阶段。  
它的职责是把已冻结的研究语义实例化成统一、可比较、可复现的截面因子合同。

## 0.1 入口身份冻结约定

`factor_role`、`factor_structure`、`portfolio_expression`、`neutralization_policy` 是 `mandate` 冻结的研究身份字段，不在本阶段重新定义。  
若 `factor_role != standalone_alpha`，必须已经在 `mandate` 中冻结 `target_strategy_reference`；若 `neutralization_policy = group_neutral`，必须已经在 `mandate` 中冻结 `group_taxonomy_reference`。  
本阶段只冻结因子表达，不改变研究身份。

---

## 1. 核心问题

**核心问题**：因子或多因子分数是否已经被定义成统一、可比较、可复现的截面面板合同。

**阶段职责**：
- 冻结 factor id 和版本
- 冻结因子方向
- 冻结 score 计算
- 冻结 coverage 和 eligibility 传递

---

## 2. 必须完成

1. 冻结 `factor_id`、`factor_version`、`factor_direction`。
2. 冻结面板主键和 `as_of_semantics`。
3. 冻结 `raw_factor_fields`、`derived_factor_fields` 和 `final_score_field`。
4. 冻结缺失值策略和 coverage contract。
5. 多因子时必须冻结确定性的组合公式，不允许 train-learned weights。
6. 若需要组内排序或组中性化，冻结 factor group context。

---

## 3. 必备输出

- `factor_panel.parquet`
- `factor_manifest.yaml`
- `factor_field_dictionary.md`
- `factor_coverage_report.parquet`
- `factor_contract.md`
- `artifact_catalog.md`
- `field_dictionary.md`

条件性输出：
- `component_factor_manifest.yaml`
- `factor_group_context.parquet`

---

## 4. Formal Gate

必须全部满足：

- `factor_id / factor_version / factor_direction` 已冻结
- `factor_panel` 可以唯一表示同一时点不同资产的因子值
- 所有输入字段都来自 `01_csf_data_ready`
- 多因子组合公式是确定性的
- 缺失值、coverage、eligibility 传递规则已写清
- 因子方向明确，不允许到 test/backtest 再解释

必须失败任一：

- 因子定义依赖 train/test/backtest 结果回写
- `factor_panel` 无法稳定重建
- 多因子组合权重在后续阶段才学习
- `factor_direction` 不清楚
- eligibility 与 factor computation 混成一团
- test 才知道的 quantile / cutoff 被偷写回 signal

---

## 5. 禁止事项

- 不得在这一层重估 train 尺子
- 不得把多因子权重放到后续阶段再学习
- 不得让同一因子在 test 之前保持方向不明
- 不得把过滤器语义伪装成独立 alpha 语义
