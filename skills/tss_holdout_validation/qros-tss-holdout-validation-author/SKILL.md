---
name: qros-tss-holdout-validation-author
description: Use when a QROS time_series_signal lineage is at the tss_holdout_validation authoring gate.
---

# TSS Holdout Validation Author

## Purpose

只在 `tss_backtest_ready review` closure 完成之后，把 `06_tss_backtest_ready` 冻结成正式 `07_tss_holdout_validation` 产物。

TSS 是“单个资产用自己的历史预测自己的未来路径/方向”，不是横截面排序；holdout 只照单验证最终冻结方案，不参与定义、筛选或调参。

## Artifact Contract Truth

- `contracts/artifacts/tss_holdout_validation_artifacts.yaml` 是本阶段 formal artifact shape 的字段真值。
- 不得把 `SKILL.md` 当作字段真值。
- 必须先读取 artifact contract，再 scaffold / build `07_tss_holdout_validation/author/formal`。
- build 后必须先运行 `qros-validate-stage --stage tss_holdout_validation`；validator 不通过不得进入 review。

## Required Inputs

- `06_tss_backtest_ready/author/formal/strategy_contract.yaml`
- `06_tss_backtest_ready/author/formal/position_timeseries.parquet`
- `06_tss_backtest_ready/review/closure/stage_completion_certificate.yaml`
- `05_tss_test_evidence/author/formal/tss_selected_variants_test.csv`

## Required Outputs

- `tss_holdout_run_manifest.json`
- `holdout_signal_diagnostics.parquet`
- `holdout_event_compare.parquet`
- `holdout_backtest_compare.parquet`
- `rolling_holdout_stability.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `window_contract`
- `reuse_contract`
- `stability_contract`
- `failure_governance`
- `delivery_contract`

## Mandatory Discipline

- 只能消费 `research_route = time_series_signal` 的上游产物。
- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。
- 不得用 holdout 调参、改阈值、改 selected variants 或回写研究问题。
- 必须照单复用 backtest 冻结策略合同，并物化 signal/event/backtest comparison。
- 必须先显式生成或刷新 lineage-local stage program，并在 `tss_holdout_run_manifest.json` 记录 replay/provenance。
- 不得写入 review/result；author lane 只能写 `author/draft`、`author/formal` 和必要的 program provenance。

## Gate Discipline

- `tss_holdout_run_manifest.json` 必须证明 holdout 只运行冻结方案。
- `holdout_signal_diagnostics.parquet` 只作为 TSS 时间序列稳定性诊断，不得改写上游选择。
- `holdout_event_compare.parquet` 和 `holdout_backtest_compare.parquet` 必须比较 single-window / merged-window / prior evidence。
- 任何 failure disposition 都必须进入 failure handling，不得在本阶段静默修复后继续推进。

## Working Rules

1. 确认 `tss_backtest_ready` review closure 已存在。
2. 读取 `contracts/artifacts/tss_holdout_validation_artifacts.yaml`。
3. 逐组确认 freeze groups，并回显 grouped summary。
4. 只有用户明确确认 `是否按以上内容冻结 tss_holdout_validation？` 后，才生成正式 artifacts。
5. 真实生成 `07_tss_holdout_validation/author/formal` 下的 required outputs。
6. 补齐 `artifact_catalog.md` 与 `field_dictionary.md`。
7. 运行 `qros-validate-stage --stage tss_holdout_validation`。
8. validator 通过后停在 `tss_holdout_validation_review_confirmation_pending`，由用户显式进入 `qros-tss-holdout-validation-review`。
