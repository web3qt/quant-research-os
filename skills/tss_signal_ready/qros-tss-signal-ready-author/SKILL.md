---
name: qros-tss-signal-ready-author
description: Use when a QROS time_series_signal lineage is at the tss_signal_ready authoring gate.
---

# TSS Signal Ready Author

## Purpose

只在 `tss_data_ready review` closure 完成之后，把 `02_tss_data_ready` 冻结成正式 `03_tss_signal_ready` 产物。

TSS 是“单个资产用自己的历史预测自己的未来路径/方向”，不是横截面排序；本阶段冻结的是单资产时间序列信号字段合同。

## Runtime Stage Admission

开始本 stage-specific author 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage tss_signal_ready --lane author`

若命令失败，必须停止；不得继续 authoring，不得补 artifact，不得绕过 `qros-research-session` 的 `current_stage`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## Artifact Contract Truth

- `contracts/artifacts/tss_signal_ready_artifacts.yaml` 是本阶段 formal artifact shape 的字段真值。
- 不得把 `SKILL.md` 当作字段真值。
- 必须先读取 artifact contract，再 scaffold / build `03_tss_signal_ready/author/formal`。
- build 后必须先运行 `qros-validate-stage --stage tss_signal_ready`；validator 不通过不得进入 review。

## Required Inputs

- `02_tss_data_ready/author/formal/time_index_manifest.json`
- `02_tss_data_ready/author/formal/asset_time_index.parquet`
- `02_tss_data_ready/author/formal/quality_flags.parquet`
- `02_tss_data_ready/review/closure/stage_completion_certificate.yaml`
- `01_mandate/author/formal/research_route.yaml`

## Required Outputs

- `signal_manifest.yaml`
- `param_manifest.csv`
- `signal_panel.parquet`
- `signal_event_panel.parquet`
- `route_inheritance_contract.yaml`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `signal_identity`
- `input_contract`
- `signal_expression`
- `event_contract`
- `delivery_contract`

## Mandatory Discipline

- 只能消费 `research_route = time_series_signal` 的上游产物。
- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。
- 只冻结单资产时间序列 signal / event schema、param identity 和 route inheritance，不得在本阶段宣布统计显著性或交易收益。
- 必须真实生成 signal panel、event panel、manifest 与 coverage/provenance，不得用 placeholder 冒充。
- 必须先显式生成或刷新 lineage-local stage program，并在 `run_manifest.json` 记录 replay/provenance。
- 不得写入 review/result；author lane 只能写 `author/draft`、`author/formal` 和必要的 program provenance。

## Gate Discipline

- `route_inheritance_contract.yaml` 必须证明 route、bar size、time split 与上游一致。
- `param_manifest.csv` 必须列出下游可能消费的 `param_id`，不能靠文件名推断。
- `signal_panel.parquet` 与 `signal_event_panel.parquet` 必须有明确 anchor time、horizon、direction 语义。
- 不得把横截面 factor score、asset rank、bucket membership 当成本阶段主产物。

## Working Rules

1. 确认 `tss_data_ready` review closure 已存在。
2. 读取 `contracts/artifacts/tss_signal_ready_artifacts.yaml`。
3. 逐组确认 freeze groups，并回显 grouped summary。
4. 只有用户明确确认 `是否按以上内容冻结 tss_signal_ready？` 后，才生成正式 artifacts。
5. 真实生成 `03_tss_signal_ready/author/formal` 下的 required outputs。
6. 补齐 `artifact_catalog.md` 与 `field_dictionary.md`。
7. 运行 `qros-validate-stage --stage tss_signal_ready`。
8. validator 通过后停在 `tss_signal_ready_review_confirmation_pending`，由用户显式进入 `qros-tss-signal-ready-review`。
