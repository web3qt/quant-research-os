# TSS Test Evidence SOP

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-TSS-TEST-EVIDENCE-v1.0 |
| 状态 | Active |
| Route | `research_route = time_series_signal` |

## 0. 文档定位

本文档解释 `05_tss_test_evidence` 的用户可见操作口径。正式字段、artifact shape 和 gate 以 `contracts/artifacts/tss_test_evidence_artifacts.yaml` 与 `contracts/stages/workflow_stage_gates.yaml` 为准。

TSS 是**单个资产用自己的历史预测自己的未来路径/方向**。它不是横截面排序，不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

## 1. 核心问题

冻结后的 TSS 信号结构是否在独立 test window 中仍有方向/路径证据。

## 2. 必须完成

- 复用 `04_tss_train_freeze` 的阈值与 variant ledger，不重估。
- 计算 event forward return 和 signal performance summary。
- 冻结 formal gate、admissibility、audit contract 和 selected variants。
- 明确哪些证据是 formal gate，哪些只是 audit-only。

## 3. 必备输出

- `event_forward_return.parquet`
- `signal_performance_summary.json`
- `tss_test_gate_table.csv`
- `tss_selected_variants_test.csv`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## 4. Formal Gate

进入 review 前必须先运行：

```bash
qros-validate-stage --stage tss_test_evidence
```

validator 不通过，不得进入 `qros-tss-test-evidence-review`。

## 5. 禁止事项

- 不得在 test window 重估 train 阈值。
- 不得看 backtest 后回写 test 白名单或 selected variants。
- 不得产出或消费 `csf_*` 横截面因子产物。
