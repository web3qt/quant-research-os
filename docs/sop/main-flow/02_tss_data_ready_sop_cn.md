# TSS Data Ready SOP（时序信号数据就绪阶段）

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-TSS-DATA-READY-v1.0 |
| 状态 | Active |
| Route | `research_route = time_series_signal` |

## 0. 文档定位

本文档解释 `02_tss_data_ready` 的用户可见操作口径。正式字段、artifact shape 和 gate 以 `contracts/artifacts/tss_data_ready_artifacts.yaml` 与 `contracts/stages/workflow_stage_gates.yaml` 为准。

TSS 是**单个资产用自己的历史预测自己的未来路径/方向**。它不是横截面排序，不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

## 1. 核心问题

原始数据能否被转换为单资产时间序列研究可复用、可审计、可重放的数据基础层。

## 2. 必须完成

- 从 `01_mandate` 继承 route、bar size、time split、universe 和数据源。
- 物化单资产或逐资产 time index，并保留缺失、stale、异常价等质量语义。
- 生成 train/test/backtest/holdout 的样本充分性说明。
- 在当前 research repo 真实生成 lineage-local stage program，不能用空目录或 placeholder 冒充完成。

## 3. 必备输出

- `time_index_manifest.json`
- `asset_time_index.parquet`
- `quality_flags.parquet`
- `split_sample_adequacy_report.yaml`
- `run_manifest.json`
- `rebuild_tss_data_ready.py`
- `artifact_catalog.md`
- `field_dictionary.md`

## 4. Formal Gate

进入 review 前必须先运行：

```bash
qros-validate-stage --stage tss_data_ready
```

validator 不通过，不得进入 `qros-tss-data-ready-review`。

## 5. 禁止事项

- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得静默 forward-fill、静默删样本或混用时间主键。
- 不得把横截面排名面板当作 `asset_time_index.parquet`。
