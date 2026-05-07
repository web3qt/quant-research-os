---
name: qros-tss-train-freeze-author
description: Use when a QROS time_series_signal lineage is at the tss_train_freeze authoring gate.
---

# TSS Train Freeze Author

## Purpose

只在 `tss_signal_ready review` closure 完成之后，把 `03_tss_signal_ready` 冻结成正式 `04_tss_train_freeze` 产物。

TSS 是“单个资产用自己的历史预测自己的未来路径/方向”，不是横截面排序；本阶段只在 train window 内冻结阈值、过滤和参数治理，不选择未来赢家。

## Runtime Stage Admission

开始本 stage-specific author 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage tss_train_freeze --lane author`

若命令失败，必须停止；不得继续 authoring，不得补 artifact，不得绕过 `qros-research-session` 的 `current_stage`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## Artifact Contract Truth

- `contracts/artifacts/tss_train_freeze_artifacts.yaml` 是本阶段 formal artifact shape 的字段真值。
- 不得把 `SKILL.md` 当作字段真值。
- 必须先读取 artifact contract，再 scaffold / build `04_tss_train_freeze/author/formal`。
- build 后必须先运行 `qros-validate-stage --stage tss_train_freeze`；validator 不通过不得进入 review。

## Required Inputs

- `03_tss_signal_ready/author/formal/signal_manifest.yaml`
- `03_tss_signal_ready/author/formal/param_manifest.csv`
- `03_tss_signal_ready/author/formal/signal_panel.parquet`
- `03_tss_signal_ready/review/closure/stage_completion_certificate.yaml`

## Required Outputs

- `tss_train_freeze.yaml`
- `train_threshold_ledger.csv`
- `train_variant_ledger.csv`
- `train_variant_rejects.csv`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `calibration_contract`
- `threshold_contract`
- `search_governance_contract`
- `reuse_contract`
- `delivery_contract`

## Mandatory Discipline

- 只能消费 `research_route = time_series_signal` 的上游产物。
- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。
- 只能使用 train window 定阈值和过滤规则，不得读取 test/backtest/holdout 结果。
- 不得根据收益最大化选择最终参数；只能冻结可检验的 train discipline 和 reject ledger。
- 必须先显式生成或刷新 lineage-local stage program，并在 `run_manifest.json` 记录 replay/provenance。
- 不得写入 review/result；author lane 只能写 `author/draft`、`author/formal` 和必要的 program provenance。

## Gate Discipline

- `tss_train_freeze.yaml` 必须冻结 window、threshold、quality filter 与 param governance。
- `train_threshold_ledger.csv` 必须说明每个阈值来源和样本窗口。
- `train_variant_ledger.csv` 与 `train_variant_rejects.csv` 必须保留搜索轨迹和拒绝原因。
- 所有 downstream variants 必须来自 `tss_signal_ready` 已冻结的 `param_manifest.csv`。

## Working Rules

1. 确认 `tss_signal_ready` review closure 已存在。
2. 读取 `contracts/artifacts/tss_train_freeze_artifacts.yaml`。
3. 逐组确认 freeze groups，并回显 grouped summary。
4. 只有用户明确确认 `是否按以上内容冻结 tss_train_freeze？` 后，才生成正式 artifacts。
5. 真实生成 `04_tss_train_freeze/author/formal` 下的 required outputs。
6. 补齐 `artifact_catalog.md` 与 `field_dictionary.md`。
7. 运行 `qros-validate-stage --stage tss_train_freeze`。
8. validator 通过后停在 `tss_train_freeze_review_confirmation_pending`，由用户显式进入 `qros-tss-train-freeze-review`。
