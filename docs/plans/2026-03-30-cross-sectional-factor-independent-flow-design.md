# Cross-Sectional Factor Independent Flow Design

**Date:** 2026-03-30  
**Status:** Approved for design handoff  
**Scope:** `cross_sectional_factor` 独立正式研究流程，覆盖 `mandate` 之后到 `holdout_validation` 之前的研究合同、review、runtime 路由和测试边界

## Goal

为 `research_route = cross_sectional_factor` 建立一条完全独立的正式研究流程，避免继续把截面因子研究强行塞进默认偏时序的 `signal_ready / train / test / backtest` 语义里。

这次设计解决的不是“如何在现有主线上加几个 if/else”，而是明确：

- 哪些阶段仍然共享治理基础设施
- 哪些阶段必须独立成截面因子专属合同
- 因子角色、组合表达和中性化口径如何成为正式冻结对象
- runtime、review skill、tests 应该如何跟着独立流程一起迁移

## Decision

不采用“同 stage 名、按 route 分流合同”的方案。  
采用“共享治理内核 + 独立 cross-sectional factor 正式流程”的方案。

原因只有一个：

统一 stage 名称看起来简单，但长期会把 reviewer 语言、runtime 检查、artifact 语义和测试模型继续绑在时序主线上，最终让 `cross_sectional_factor` 永远是附属路线，而不是独立研究框架。

## Shared Vs Independent

### Shared Governance Layer

以下对象继续共享：

- `idea_intake`
- `mandate`
- `promotion_decision`
- lineage / rollback / child lineage 纪律
- transition approval artifacts
- `review_findings.yaml`
- `artifact_catalog.md`
- `field_dictionary.md`
- review status vocabulary

### Independent Research Flow

一旦 `mandate` 冻结：

```text
research_route = cross_sectional_factor
```

正式进入独立流程：

```text
01_csf_data_ready
02_csf_signal_ready
03_csf_train_freeze
04_csf_test_evidence
05_csf_backtest_ready
06_csf_holdout_validation
```

不再复用旧的时序 stage 名称作为正式真值。

## Independent Stage Map

### `01_csf_data_ready`

核心问题：

能否形成稳定、可审计的 `date x asset` 截面研究底座，而不是零散的单资产时间序列表。

### `02_csf_signal_ready`

核心问题：

因子或多因子分数是否已经被定义成统一、可比较、可复现的截面面板合同。

### `03_csf_train_freeze`

核心问题：

截面因子的预处理、标准化、中性化、分组和再平衡口径如何在 train 内冻结。

### `04_csf_test_evidence`

核心问题：

冻结后的截面排序能力，或截面 filter / combo 条件改善能力，是否在独立样本仍然成立。

### `05_csf_backtest_ready`

核心问题：

冻结后的因子分数映射成正式组合后，是否具备成本后的经济可行性。

### `06_csf_holdout_validation`

核心问题：

最终冻结方案在最后完全未参与设计的窗口里，是否仍然没有翻向或塌陷。

## Route State Model

独立截面因子流程至少冻结以下路线级字段：

- `research_route = cross_sectional_factor`
- `factor_role = standalone_alpha | regime_filter | combo_filter`
- `factor_structure = single_factor | multi_factor_score`
- `portfolio_expression = long_short_market_neutral | long_only_rank`
- `neutralization_policy = none | market_beta_neutral | group_neutral`

这些字段不是实现细节，而是研究身份的一部分。

### Child Lineage Triggers

下列变化默认触发 `CHILD LINEAGE`：

- `factor_role` 改变
- `portfolio_expression` 改变
- `neutralization_policy` 的大类改变
- 研究对象从截面排序改为单资产方向

## Mandate Freeze Additions

`mandate` 必须冻结：

- `factor_role`
- `factor_structure`
- `portfolio_expression`
- `neutralization_policy`
- `universe_definition`
- `rebalance_frequency`
- `holding_horizon_set`
- `cross_section_time_key`
- `ranking_objective`
- `primary_evidence_contract`
- `capacity_audit_basis`

条件性字段：

- 当 `factor_role != standalone_alpha` 时，必须冻结 `target_strategy_reference`
- 当 `neutralization_policy = group_neutral` 时，必须冻结 `group_taxonomy_reference`

## `01_csf_data_ready` Contract

### Required Artifacts

- `panel_manifest.json`
- `asset_universe_membership.parquet`
- `cross_section_coverage.parquet`
- `eligibility_base_mask.parquet`
- `shared_feature_base/`
- `csf_data_contract.md`
- `artifact_catalog.md`
- `field_dictionary.md`

条件性 artifact：

- `asset_taxonomy_snapshot.*`，当后续允许 `group_neutral`

### Formal Gate

必须全部满足：

- 面板主键明确且唯一：`date + asset`
- 同一日期的截面覆盖可审计
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

## `02_csf_signal_ready` Contract

### Required Signal Fields

- `factor_id`
- `factor_version`
- `factor_direction`
- `panel_primary_key`
- `as_of_semantics`
- `universe_membership_rule`
- `eligibility_mask_rule`
- `coverage_contract`
- `raw_factor_fields`
- `derived_factor_fields`
- `final_score_field`
- `missing_value_policy`

### Required Artifacts

- `factor_panel.parquet`
- `factor_manifest.yaml`
- `factor_field_dictionary.md`
- `factor_coverage_report.parquet`
- `factor_contract.md`
- `artifact_catalog.md`
- `field_dictionary.md`

条件性 artifact：

- `component_factor_manifest.yaml`，当 `factor_structure = multi_factor_score`
- `factor_group_context.parquet`，当需要组内排序或 `group_neutral`

### Formal Gate

必须全部满足：

- `factor_id / factor_version / factor_direction` 已冻结
- `factor_panel` 可以唯一表示同一时点不同资产的因子值
- 所有输入字段都来自已冻结 `01_csf_data_ready`
- 多因子组合公式是确定性的，不允许 train-learned weights
- 缺失值、coverage、eligibility 传递规则已写清
- 因子方向明确，不允许到 test/backtest 再解释

必须失败任一：

- 因子定义依赖 train/test/backtest 结果回写
- `factor_panel` 无法稳定重建
- 多因子组合权重在后续阶段才学习
- `factor_direction` 不清楚
- eligibility 与 factor computation 混成一团
- test 才知道的 quantile / cutoff 被偷写回 signal

## `03_csf_train_freeze` Contract

### Frozen Groups

- `preprocess_contract`
- `neutralization_contract`
- `ranking_bucket_contract`
- `rebalance_contract`
- `eligibility_quality_contract`
- `search_governance_contract`

### Required Artifacts

- `csf_train_freeze.yaml`
- `train_factor_quality.parquet`
- `train_variant_ledger.csv`
- `train_variant_rejects.csv`
- `train_bucket_diagnostics.parquet`
- `csf_train_contract.md`
- `artifact_catalog.md`
- `field_dictionary.md`

条件性 artifact：

- `train_neutralization_diagnostics.parquet`，当存在 neutralization

### Formal Gate

必须全部满足：

- preprocess、standardize、neutralize、bucket、rebalance、eligibility 全部冻结
- 所有 train variant 都有身份记录
- reject 不是静默丢弃，而是显式记账
- downstream test 只能复用 frozen train rules
- neutralization 如存在，必须有独立合同和诊断

必须失败任一：

- 根据 test/backtest 结果回写 train 口径
- 只有保留者，没有 reject ledger
- quantile / bucket 规则未冻结
- neutralization 存在但没有独立合同
- rebalance / lag / overlap 口径未冻结
- 在 train 内直接用收益最大化选 final winner

### Discipline

`03_csf_train_freeze` 可以比较 variant，但不能宣布最终 champion；只能冻结 admissible set。

## `04_csf_test_evidence` Contract

`factor_role` 在这一层开始正式分流。

### `standalone_alpha`

主证据：

- `Rank IC`
- `ICIR`
- bucket / quantile return spread
- monotonicity
- breadth
- subperiod stability

必备 artifact：

- `rank_ic_timeseries.parquet`
- `rank_ic_summary.json`
- `bucket_returns.parquet`
- `monotonicity_report.json`
- `breadth_coverage_report.parquet`
- `subperiod_stability_report.json`
- `csf_test_gate_table.csv`
- `csf_selected_variants_test.csv`
- `csf_test_contract.md`

必须全部满足：

- 只复用 `03_csf_train_freeze` 的 frozen rules
- `Rank IC` 方向与 `factor_direction` 一致
- 至少一类主要排序证据成立：`Rank IC` 或 bucket spread
- 单调性未完全崩塌
- breadth / coverage 不是极窄样本支撑
- 子窗口未明显翻向

### `regime_filter | combo_filter`

主证据：

- gated vs ungated 改善
- drawdown 改善
- tail risk 改善
- 稳定性改善
- 覆盖率不过低

必备 artifact：

- `filter_condition_panel.parquet`
- `target_strategy_condition_compare.parquet`
- `gated_vs_ungated_summary.json`
- `drawdown_compare.json`
- `tail_risk_compare.json`
- `coverage_participation_report.parquet`
- `csf_test_gate_table.csv`
- `csf_selected_variants_test.csv`
- `csf_test_contract.md`

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

## `05_csf_backtest_ready` Contract

### Supported Portfolio Expressions

第一版只正式支持：

- `long_short_market_neutral`
- `long_only_rank`

### Frozen Portfolio Fields

- `portfolio_expression`
- `selection_rule`
- `weight_mapping_rule`
- `gross_exposure_rule`
- `net_exposure_rule`
- `turnover_budget_rule`
- `rebalance_execution_lag`
- `cost_model`
- `capacity_model`
- `max_name_weight_rule`

额外字段：

- `long_bucket_definition / short_bucket_definition / dollar_neutral_rule / beta_neutral_tolerance / group_neutral_overlay` for `long_short_market_neutral`
- `long_selection_cut / cash_policy / concentration_cap_rule` for `long_only_rank`

### Required Artifacts

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

条件性 artifact：

- `target_strategy_compare.parquet`
- `gated_portfolio_summary.parquet`
- `ungated_portfolio_summary.parquet`

### Formal Gate

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

## `06_csf_holdout_validation` Contract

### Required Artifacts

- `csf_holdout_run_manifest.json`
- `holdout_factor_diagnostics.parquet`
- `holdout_test_compare.parquet`
- `holdout_portfolio_compare.parquet`
- `rolling_holdout_stability.json`
- `regime_shift_audit.json`
- `csf_holdout_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

### Formal Gate

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

## Review And Skill Changes

需要新增一套独立 skill：

- `qros-csf-data-ready-author`
- `qros-csf-data-ready-review`
- `qros-csf-signal-ready-author`
- `qros-csf-signal-ready-review`
- `qros-csf-train-freeze-author`
- `qros-csf-train-freeze-review`
- `qros-csf-test-evidence-author`
- `qros-csf-test-evidence-review`
- `qros-csf-backtest-ready-author`
- `qros-csf-backtest-ready-review`
- `qros-csf-holdout-validation-author`
- `qros-csf-holdout-validation-review`

共享 skill 继续保留：

- `qros-idea-intake-author`
- `qros-mandate-author`
- `qros-mandate-review`
- `qros-research-session`

## Runtime Implications

runtime 必须显式支持：

- `mandate` 之后根据 `research_route` 进入时序主线或 CSF 主线
- `csf_*` stages 的独立 required outputs
- `csf_*` stages 的独立 closure 检查
- status 输出中的 `factor_role` 和 `portfolio_expression`

不得再靠“进入旧 stage 后再 if/else 分流”来模拟独立流程。

## Testing Implications

建议新增独立测试文件，而不是继续向时序测试追加条件分支：

- `tests/test_csf_data_ready_runtime.py`
- `tests/test_csf_signal_ready_runtime.py`
- `tests/test_csf_train_freeze_runtime.py`
- `tests/test_csf_test_evidence_runtime.py`
- `tests/test_csf_backtest_ready_runtime.py`
- `tests/test_csf_holdout_runtime.py`
- `tests/test_csf_research_session_routing.py`

共享测试只保留治理前置层：

- `idea_intake -> mandate -> route freeze`
- mandate 后 route-based stage routing

## Non-Goals

本次设计明确不做：

- `event_trigger`
- `relative_value`
- 更复杂的风险模型或风格模型
- train-learned 多因子权重优化
- live execution / production admission 改造

## Acceptance Criteria

这套独立流程落地后，至少要满足：

1. `research_route = cross_sectional_factor` 时，runtime 不再进入旧的时序 `signal_ready / train / test / backtest`
2. `workflow_stage_gates.yaml` 里存在独立 `csf_*` stages 作为 formal gate 真值
3. `factor_role / factor_structure / portfolio_expression / neutralization_policy` 成为正式冻结对象
4. `standalone_alpha` 与 `regime_filter | combo_filter` 在 `04_csf_test_evidence` 的证据语义分离
5. `05_csf_backtest_ready` 只支持批准过的组合表达，并 machine-readable 冻结
6. `csf_*` review skills 和 tests 独立存在，不再依赖时序主线的隐式默认语义

## Expected Outcome

更新后，研究员在 `mandate` 一旦确定 `cross_sectional_factor`，就会进入一条完全独立的正式流程；系统不再把截面研究当成“时序主线上的一种变体”，而是把它当作拥有独立样本单位、独立证据语义、独立组合表达和独立回退纪律的正式研究框架。
