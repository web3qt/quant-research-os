# CSF Data Ready SOP

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-CSF-DATA-READY-v1.0 |
| 日期 | 2026-03-30 |
| 状态 | Active |

---

## 0. 文档定位

本文档定义 `research_route = cross_sectional_factor` 时的 `01_csf_data_ready` 阶段。  
它不再沿用旧的时序 Data Ready 语义，而是为横截面研究冻结 `date x asset` 面板底座、universe membership 和 eligibility mask。

## 0.1 入口身份冻结约定

`factor_role`、`factor_structure`、`portfolio_expression`、`neutralization_policy` 是 `mandate` 冻结的研究身份字段，不在本阶段重新定义。  
若 `factor_role != standalone_alpha`，必须已经在 `mandate` 中冻结 `target_strategy_reference`；若 `neutralization_policy = group_neutral`，必须已经在 `mandate` 中冻结 `group_taxonomy_reference`。  
本阶段只消费这些身份字段，不重写它们。

---

## 1. 核心问题

**核心问题**：能否形成稳定、可审计、可复用的截面研究底座，而不是零散的单资产时序表。

**阶段职责**：
- 冻结截面面板主键
- 冻结 universe membership
- 冻结 eligibility base mask
- 冻结共享字段底座

---

## 2. 必须完成

1. 定义 `date x asset` 面板主键。
2. 显式记录每个日期的 universe membership。
3. 显式记录 eligibility base mask，不得把可研究性逻辑藏进后续因子代码。
4. 冻结截面覆盖率和缺失语义。
5. 若后续允许 `group_neutral`，冻结或版本化 group taxonomy。

---

## 3. 必备输出

- `panel_manifest.json`
- `asset_universe_membership.parquet`
- `cross_section_coverage.parquet`
- `eligibility_base_mask.parquet`
- `shared_feature_base/`
- `csf_data_contract.md`
- `artifact_catalog.md`
- `field_dictionary.md`

条件性输出：
- `asset_taxonomy_snapshot.*`

---

## 4. Formal Gate

必须全部满足：

- 面板主键明确且唯一：`date + asset`
- 截面覆盖可审计
- universe membership 显式记录
- eligibility mask 作为独立底座存在
- 共享字段具备时间语义和缺失语义
- 如允许 `group_neutral`，taxonomy 已冻结或显式版本化

必须失败任一：

- 只有资产时序表，没有显式截面面板合同
- universe membership 无法按日期重建
- eligibility 规则混在下游因子代码里
- 覆盖率波动显著却没有报告
- 分组中性化需要的 taxonomy 在下游临时补

---

## 5. 禁止事项

- 不得在这一层定义正式因子
- 不得在这一层做 train 样本统计尺子
- 不得把覆盖率差异静默吞掉
- 不得把可研究性判断推迟到 signal_ready
