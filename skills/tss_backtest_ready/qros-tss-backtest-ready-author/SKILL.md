---
name: qros-tss-backtest-ready-author
description: Use when a QROS time_series_signal lineage is at the tss_backtest_ready authoring gate.
---

# TSS Backtest Ready Author

## Purpose

只在 `tss_test_evidence review` closure 完成之后，把 `05_tss_test_evidence` 冻结成正式 `06_tss_backtest_ready` 产物。

TSS 是“单个资产用自己的历史预测自己的未来路径/方向”，不是横截面排序；本阶段验证冻结信号能否转成可复现、可交易的时间序列策略证据。

## Runtime Stage Admission

开始本 stage-specific author 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage tss_backtest_ready --lane author`

若命令失败，必须停止；不得继续 authoring，不得补 artifact，不得绕过 `qros-research-session` 的 `current_stage`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## Artifact Contract Truth

- `contracts/artifacts/tss_backtest_ready_artifacts.yaml` 是本阶段 formal artifact shape 的字段真值。
- 不得把 `SKILL.md` 当作字段真值。
- 必须先读取 artifact contract，再 scaffold / build `06_tss_backtest_ready/author/formal`。
- build 后必须先运行 `qros-validate-stage --stage tss_backtest_ready`；validator 不通过不得进入 review。

## Required Inputs

- `05_tss_test_evidence/author/formal/tss_selected_variants_test.csv`
- `05_tss_test_evidence/review/closure/stage_completion_certificate.yaml`
- `04_tss_train_freeze/author/formal/tss_train_freeze.yaml`
- `03_tss_signal_ready/author/formal/signal_panel.parquet`

## Required Outputs

- `strategy_contract.yaml`
- `engine_compare.csv`
- `position_timeseries.parquet`
- `trade_ledger.csv`
- `tss_backtest_gate_table.csv`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `strategy_contract`
- `execution_contract`
- `risk_contract`
- `diagnostic_contract`
- `delivery_contract`

## Mandatory Discipline

- 只能消费 `research_route = time_series_signal` 的上游产物。
- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。
- 不得在 backtest 阶段重新选参数、重估阈值或回写 test 证据。
- 必须物化 position timeseries、trade ledger、engine compare 和 capacity/成本相关 gate 证据。
- 必须先显式生成或刷新 lineage-local stage program，并在 `run_manifest.json` 记录 replay/provenance。
- 不得写入 review/result；author lane 只能写 `author/draft`、`author/formal` 和必要的 program provenance。

## Gate Discipline

- `strategy_contract.yaml` 必须冻结执行、成本、仓位和风险口径。
- `engine_compare.csv` 必须说明主要执行引擎与对照引擎是否语义一致。
- `position_timeseries.parquet` 与 `trade_ledger.csv` 必须可追溯到已冻结 variants。
- `tss_backtest_gate_table.csv` 必须分清 formal gate、异常收益复核和 audit-only。

## Working Rules

1. 确认 `tss_test_evidence` review closure 已存在。
2. 读取 `contracts/artifacts/tss_backtest_ready_artifacts.yaml`。
3. 逐组确认 freeze groups，并回显 grouped summary。
4. 只有用户明确确认 `是否按以上内容冻结 tss_backtest_ready？` 后，才生成正式 artifacts。
5. 真实生成 `06_tss_backtest_ready/author/formal` 下的 required outputs。
6. 补齐 `artifact_catalog.md` 与 `field_dictionary.md`。
7. 运行 `qros-validate-stage --stage tss_backtest_ready`。
8. validator 通过后停在 `tss_backtest_ready_review_confirmation_pending`，由用户显式进入 `qros-tss-backtest-ready-review`。
