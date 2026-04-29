---
name: qros-tss-test-evidence-review
description: Use when a QROS time_series_signal lineage is ready for explicit tss_test_evidence review.
---

# TSS Test Evidence Review

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

`qros-review` 是唯一 deterministic closer。

## 独立 reviewer 子代理要求

- 进入本 skill 后，必须在当前会话中用 `spawn_agent` 拉起独立 reviewer 子代理，且 `fork_context` 必须是 `false`。
- reviewer 子代理创建后，主线程优先运行 `./.qros/bin/qros-review-cycle prepare`。
- reviewer 子代理只允许读取 `review/request/*` 与 `author/formal/*`。
- reviewer 子代理只允许写入 `review/result/reviewer_findings.raw.yaml`。
- reviewer 子代理不得修改 author/formal。
- reviewer 完成后，主线程必须运行 `./.qros/bin/qros-review`。

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/artifacts/tss_test_evidence_artifacts.yaml`
- `artifact_catalog.md`
- `field_dictionary.md`
- `run_manifest.json`

## 必需输入

- `04_tss_train_freeze/review/closure/stage_completion_certificate.yaml`
- `05_tss_test_evidence/author/formal/event_forward_return.parquet`
- `05_tss_test_evidence/author/formal/signal_performance_summary.json`
- `05_tss_test_evidence/author/formal/tss_test_gate_table.csv`
- `05_tss_test_evidence/author/formal/tss_selected_variants_test.csv`
- `05_tss_test_evidence/author/formal/split_threshold_attestation.yaml`
- `05_tss_test_evidence/author/formal/selected_variant_membership_proof.csv`
- `05_tss_test_evidence/author/formal/upstream_binding_digest_ledger.yaml`

## 必需输出

- `review/result/reviewer_findings.raw.yaml`
- `review/result/adversarial_review_result.yaml`
- `review/result/review_findings.yaml`
- `review/closure/stage_completion_certificate.yaml`

## 正式门禁

- 进入 reviewer lane 前必须已经运行 `qros-validate-stage --stage tss_test_evidence`。
- 进入 reviewer lane 前必须通过 deterministic preflight；ARTIFACT-CONTRACT-001 与 TSS-TEST-SEMANTIC-001 都是 review 前阻断项。
- `adversarial_review_request.yaml` 中 `upstream_binding_artifact_paths` 不得为空，且必须包含本阶段 proof artifacts。
- 只能审查 `research_route = time_series_signal` 的 `05_tss_test_evidence` 产物。
- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

## 审查清单

- [blocking] test window 独立于 train，且阈值未重估。
- [blocking] forward return 对齐无前视。
- [blocking] selected variants 全部来自 train freeze。
- [blocking] formal gate 与 audit-only 证据分离。
- [blocking] 没有把横截面排名指标当作单资产 TSS 主证据。

## Rollback 规则

- 默认 rollback stage：`tss_test_evidence`。
- 允许修改：补全统计表、修正对齐说明、修复 stage program。
- 若需要改 train 阈值或 signal schema，必须回退对应上游阶段或开 child lineage。

## 下游权限

- 通过 closure 后可进入 `tss_backtest_ready_confirmation_pending`。
- 下游只能消费 test 选定且仍符合 train freeze 的 variants。

## 执行顺序

1. 完成 review-ready 自查并确认 handoff scope 是当前 author outputs。
2. 运行 `qros-validate-stage --stage tss_test_evidence`。
3. 用 `spawn_agent` 创建独立 reviewer 子代理。
4. 运行 `./.qros/bin/qros-review-cycle prepare`。
5. 用 `send_input` 交付 handoff。
6. 等待 reviewer 只写 `review/result/reviewer_findings.raw.yaml`。
7. 运行 `./.qros/bin/qros-review` 完成 closure。
