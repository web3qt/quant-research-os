---
name: qros-tss-test-evidence-author
description: Use when a QROS time_series_signal lineage is at the tss_test_evidence authoring gate.
---

# TSS Test Evidence Author

## Purpose

只在 `tss_train_freeze review` closure 完成之后，把 `04_tss_train_freeze` 冻结成正式 `05_tss_test_evidence` 产物。

TSS 是“单个资产用自己的历史预测自己的未来路径/方向”，不是横截面排序；本阶段用独立 test window 验证 train 冻结后的方向/路径证据，不重新定尺子。

## Artifact Contract Truth

- `contracts/artifacts/tss_test_evidence_artifacts.yaml` 是本阶段 formal artifact shape 的字段真值。
- 不得把 `SKILL.md` 当作字段真值。
- 必须先读取 artifact contract，再 scaffold / build `05_tss_test_evidence/author/formal`。
- build 后必须先运行 `qros-validate-stage --stage tss_test_evidence`；validator 不通过不得进入 review。

## Required Inputs

- `04_tss_train_freeze/author/formal/tss_train_freeze.yaml`
- `04_tss_train_freeze/author/formal/train_variant_ledger.csv`
- `04_tss_train_freeze/review/closure/stage_completion_certificate.yaml`
- `03_tss_signal_ready/author/formal/signal_event_panel.parquet`

## Required Outputs

- `event_forward_return.parquet`
- `signal_performance_summary.json`
- `tss_test_gate_table.csv`
- `tss_selected_variants_test.csv`
- `run_manifest.json`
- `artifact_catalog.md`
- `field_dictionary.md`

## Freeze Groups

必须按 5 组推进：

- `window_contract`
- `variant_contract`
- `evidence_contract`
- `audit_contract`
- `delivery_contract`

## Mandatory Discipline

- 只能消费 `research_route = time_series_signal` 的上游产物。
- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。
- 必须复用 train 冻结阈值，不得在 test window 重估。
- Test 只验证结构和方向，不得因为结果好坏回写 signal 或 train。
- 必须先显式生成或刷新 lineage-local stage program，并在 `run_manifest.json` 记录 replay/provenance。
- 不得写入 review/result；author lane 只能写 `author/draft`、`author/formal` 和必要的 program provenance。

## Gate Discipline

- `event_forward_return.parquet` 必须按冻结 anchor/horizon 计算，不能前视。
- `signal_performance_summary.json` 必须解释 TSS 方向/路径证据和残留风险。
- `tss_test_gate_table.csv` 必须分清 formal gate 与 audit-only。
- `tss_selected_variants_test.csv` 只能从 train 冻结 variant 中筛选，不能新增 param_id。

## Working Rules

1. 确认 `tss_train_freeze` review closure 已存在。
2. 读取 `contracts/artifacts/tss_test_evidence_artifacts.yaml`。
3. 逐组确认 freeze groups，并回显 grouped summary。
4. 只有用户明确确认 `是否按以上内容冻结 tss_test_evidence？` 后，才生成正式 artifacts。
5. 真实生成 `05_tss_test_evidence/author/formal` 下的 required outputs。
6. 补齐 `artifact_catalog.md` 与 `field_dictionary.md`。
7. 运行 `qros-validate-stage --stage tss_test_evidence`。
8. validator 通过后停在 `tss_test_evidence_review_confirmation_pending`，由用户显式进入 `qros-tss-test-evidence-review`。
