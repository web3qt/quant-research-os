# TSS Holdout Validation SOP

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-TSS-HOLDOUT-VALIDATION-v1.0 |
| 状态 | Active |
| Route | `research_route = time_series_signal` |

## 0. 文档定位

本文档解释 `07_tss_holdout_validation` 的用户可见操作口径。正式字段、artifact shape 和 gate 以 `contracts/artifacts/tss_holdout_validation_artifacts.yaml` 与 `contracts/stages/workflow_stage_gates.yaml` 为准。

TSS 是**单个资产用自己的历史预测自己的未来路径/方向**。它不是横截面排序，不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

## 1. 核心问题

最终冻结的 TSS 方案在完全未参与设计、筛选、训练和回测调参的 holdout window 中是否仍未翻向。

## 2. 必须完成

- 照单复用 `06_tss_backtest_ready` 的 strategy contract。
- 冻结 window contract、reuse contract、stability contract、failure governance。
- 物化 holdout signal diagnostics、event comparison、backtest comparison。
- 如果出现 failure disposition，转入 failure handling，不在原线静默修复后继续推进。

## 3. 必备输出

- `tss_holdout_run_manifest.json`
- `holdout_signal_diagnostics.parquet`
- `holdout_event_compare.parquet`
- `holdout_backtest_compare.parquet`
- `rolling_holdout_stability.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## 4. Formal Gate

进入 review 前必须先运行：

```bash
qros-validate-stage --stage tss_holdout_validation
```

validator 不通过，不得进入 `qros-tss-holdout-validation-review`。

## 5. 禁止事项

- 不得用 holdout 调参、改阈值、改 selected variants 或回写研究问题。
- 不得把 holdout 并入 test/backtest。
- 不得产出或消费 `csf_*` 横截面因子产物。
