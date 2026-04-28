# TSS Backtest Ready SOP

| 字段 | 值 |
|------|-----|
| Doc ID | SOP-TSS-BACKTEST-READY-v1.0 |
| 状态 | Active |
| Route | `research_route = time_series_signal` |

## 0. 文档定位

本文档解释 `06_tss_backtest_ready` 的用户可见操作口径。正式字段、artifact shape 和 gate 以 `contracts/artifacts/tss_backtest_ready_artifacts.yaml` 与 `contracts/stages/workflow_stage_gates.yaml` 为准。

TSS 是**单个资产用自己的历史预测自己的未来路径/方向**。它不是横截面排序，不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

## 1. 核心问题

test closure 后允许的 TSS variants 能否转成可复现、可交易、可审计的策略执行证据。

## 2. 必须完成

- 冻结 execution policy、portfolio policy、risk overlay、engine contract。
- 只使用 `05_tss_test_evidence` 允许的 selected variants。
- 物化 position timeseries、trade ledger、engine compare 和 backtest gate table。
- 对异常收益、成本、滑点和容量风险进行正式复核。

## 3. 必备输出

- `strategy_contract.yaml`
- `engine_compare.csv`
- `position_timeseries.parquet`
- `trade_ledger.csv`
- `tss_backtest_gate_table.csv`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## 4. Formal Gate

进入 review 前必须先运行：

```bash
qros-validate-stage --stage tss_backtest_ready
```

validator 不通过，不得进入 `qros-tss-backtest-ready-review`。

## 5. 禁止事项

- 不得在 backtest 重新选参数、重估阈值或回写 test。
- 不得在异常收益复核未完成时写 PASS。
- 不得产出或消费 `csf_*` 横截面因子产物。
