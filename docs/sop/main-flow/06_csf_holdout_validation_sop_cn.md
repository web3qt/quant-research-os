# CSF Holdout Validation SOP

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-CSF-HOLDOUT-VALIDATION-v1.0 |
| 日期 | 2026-03-30 |
| 状态 | Active |

---

## 0. 文档定位

本文档定义 `research_route = cross_sectional_factor` 时的 `06_csf_holdout_validation` 阶段。  
这一层只验证冻结方案在最后完全未参与设计的窗口里是否仍然稳定。

## 0.1 入口身份冻结约定

`factor_role`、`factor_structure`、`portfolio_expression`、`neutralization_policy` 是 `mandate` 冻结的研究身份字段，不在本阶段重新定义。  
若 `factor_role != standalone_alpha`，必须已经在 `mandate` 中冻结 `target_strategy_reference`；若 `neutralization_policy = group_neutral`，必须已经在 `mandate` 中冻结 `group_taxonomy_reference`。  
本阶段只验证最终冻结方案，不改变研究身份与路线。

---

## 1. 核心问题

**核心问题**：最终冻结方案在最后完全未参与设计的窗口里，是否仍然没有翻向或塌陷。

**阶段职责**：
- 复用冻结方案，不再重估
- 比较 holdout 与 test / backtest
- 审计 regime shift
- 冻结最终 holdout 结论

---

## 2. 必备输出

- `csf_holdout_run_manifest.json`
- `holdout_factor_diagnostics.parquet`
- `holdout_test_compare.parquet`
- `holdout_portfolio_compare.parquet`
- `rolling_holdout_stability.json`
- `regime_shift_audit.json`
- `csf_holdout_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

---

## 3. Formal Gate

必须全部满足：

- 只复用冻结方案，不重估上游尺子
- 主要方向未翻向
- 退化可解释且未超过容忍边界
- holdout 覆盖和 breadth 未塌到不可解释
- regime shift 明显时，必须显式审计

必须失败任一：

- 在 holdout 调参
- 在 holdout 改 bucket cut、neutralization、weight mapping
- 主要证据翻向
- 结果只靠极少数窗口支撑
- regime shift 明显却没有审计结论

---

## 4. 禁止事项

- 不得把 holdout 当成再训练窗口
- 不得在 holdout 回写任何前序冻结字段
- 不得把 holdout 的分布漂移静默归因成策略失效
- 不得把 holdout 并入 test 或 backtest
