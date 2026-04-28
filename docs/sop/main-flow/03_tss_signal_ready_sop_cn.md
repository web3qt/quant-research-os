# TSS Signal Ready SOP

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-TSS-SIGNAL-READY-v1.0 |
| 状态 | Active |
| Route | `research_route = time_series_signal` |

## 0. 文档定位

本文档解释 `03_tss_signal_ready` 的用户可见操作口径。正式字段、artifact shape 和 gate 以 `contracts/artifacts/tss_signal_ready_artifacts.yaml` 与 `contracts/stages/workflow_stage_gates.yaml` 为准。

TSS 是**单个资产用自己的历史预测自己的未来路径/方向**。它不是横截面排序，不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

## 1. 核心问题

研究对象是否已被物化为统一、可复现、可比较的单资产时间序列 signal / event schema。

## 2. 必须完成

- 从 `02_tss_data_ready` 继承 time index、quality semantics 和 split 边界。
- 冻结 signal expression、param identity、time semantics、signal schema。
- 物化 `signal_panel.parquet` 与 `signal_event_panel.parquet`。
- 写清 route inheritance，证明没有漂移成 `cross_sectional_factor`。

## 3. 必备输出

- `signal_manifest.yaml`
- `param_manifest.csv`
- `signal_panel.parquet`
- `signal_event_panel.parquet`
- `route_inheritance_contract.yaml`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## 4. Formal Gate

进入 review 前必须先运行：

```bash
qros-validate-stage --stage tss_signal_ready
```

validator 不通过，不得进入 `qros-tss-signal-ready-review`。

## 5. 禁止事项

- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得在 Train 阶段临时新增本阶段未物化的 `param_id`。
- 不得把 asset rank、factor score、bucket membership 当作 TSS 主产物。
