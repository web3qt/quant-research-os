# TSS Train Freeze SOP（时序信号训练冻结阶段）

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-TSS-TRAIN-FREEZE-v1.0 |
| 状态 | Active |
| Route | `research_route = time_series_signal` |

## 0. 文档定位

本文档解释 `04_tss_train_freeze` 的用户可见操作口径。正式字段、artifact shape 和 gate 以 `contracts/artifacts/tss_train_freeze_artifacts.yaml` 与 `contracts/stages/workflow_stage_gates.yaml` 为准。

TSS 是**单个资产用自己的历史预测自己的未来路径/方向**。它不是横截面排序，不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

## 1. 核心问题

如何只使用 train window 把 TSS 的阈值、质量过滤和候选 variant 治理冻结下来。

## 2. 必须完成

- 复用 `03_tss_signal_ready` 已冻结的 signal schema 和 `param_manifest.csv`。
- 冻结 window contract、threshold contract、quality filters、param governance。
- 记录所有 train variants、rejects 和拒绝原因。
- 保证 train 不读取 test/backtest/holdout。

## 3. 必备输出

- `tss_train_freeze.yaml`
- `train_threshold_ledger.csv`
- `train_variant_ledger.csv`
- `train_variant_rejects.csv`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## 4. Formal Gate

进入 review 前必须先运行：

```bash
qros-validate-stage --stage tss_train_freeze
```

validator 不通过，不得进入 `qros-tss-train-freeze-review`。

## 5. 禁止事项

- 不得根据 test/backtest/holdout 回写 train 阈值。
- 不得用收益最大化选择最终参数。
- 不得产出或消费 `csf_*` 横截面因子产物。
