---
name: qros-tss-holdout-validation-review
description: Use when a QROS time_series_signal lineage is ready for explicit tss_holdout_validation review.
---

# TSS Holdout Validation Review

## Runtime Stage Admission

开始本 stage-specific review 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage tss_holdout_validation --lane review`

若命令失败，必须停止；不得继续 review，不得启动 reviewer，不得运行 `qros-review-cycle prepare`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

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

reviewer 写出的 `reviewer_findings.raw.yaml` 必须包含以下顶层字段：

- `review_cycle_id: copy the literal review cycle value printed in the reviewer handoff`
- `reviewer_agent_id: copy the literal reviewer agent id printed in the reviewer handoff`
- `review_loop_outcome: one of FIX_REQUIRED, CLOSURE_READY_PASS, CLOSURE_READY_CONDITIONAL_PASS, CLOSURE_READY_PASS_FOR_RETRY, CLOSURE_READY_RETRY, CLOSURE_READY_NO_GO, CLOSURE_READY_CHILD_LINEAGE`
- `blocking_findings: []`
- `reservation_findings: []`
- `info_findings: []`
- `residual_risks: []`

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/artifacts/tss_holdout_validation_artifacts.yaml`
- `artifact_catalog.md`
- `field_dictionary.md`
- `tss_holdout_run_manifest.json`

## 必需输入

- `06_tss_backtest_ready/review/closure/stage_completion_certificate.yaml`
- `07_tss_holdout_validation/author/formal/tss_holdout_run_manifest.json`
- `07_tss_holdout_validation/author/formal/holdout_signal_diagnostics.parquet`
- `07_tss_holdout_validation/author/formal/holdout_event_compare.parquet`
- `07_tss_holdout_validation/author/formal/holdout_backtest_compare.parquet`
- `07_tss_holdout_validation/author/formal/rolling_holdout_stability.json`

## 必需输出

- `review/result/reviewer_findings.raw.yaml`
- `review/result/adversarial_review_result.yaml`
- `review/result/review_findings.yaml`
- `review/closure/stage_completion_certificate.yaml`

## 正式门禁

- 进入 reviewer lane 前必须已经运行 `qros-validate-stage --stage tss_holdout_validation`。
- 只能审查 `research_route = time_series_signal` 的 `07_tss_holdout_validation` 产物。
- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

## 审查清单

- [blocking] holdout 完全未参与上游定义、筛选、阈值或策略合同。
- [blocking] run manifest 证明只照单执行冻结方案。
- [blocking] signal/event/backtest comparison 可解释退化、翻向或 regime 差异。
- [blocking] failure governance 已明确；不允许静默修复后继续推进。
- [blocking] author outputs 非 placeholder，且 provenance 可重放。

## Rollback 规则

- 默认 rollback stage：`tss_holdout_validation`。
- 允许修改：补全 comparison artifact、修正运行账本、修复 stage program。
- 若 holdout 需要改变策略、参数、阈值或研究问题，必须走 failure handling / child lineage。

## 下游权限

- `tss_holdout_validation review` 是当前 TSS 单入口流程终点。
- closure 只能证明本 lineage 完成 holdout；不得自动开启新研究线。

## 执行顺序

1. 完成 review-ready 自查并确认 handoff scope 是当前 author outputs。
2. 运行 `qros-validate-stage --stage tss_holdout_validation`。
3. 用 `spawn_agent` 创建独立 reviewer 子代理。
4. 运行 `./.qros/bin/qros-review-cycle prepare`。
5. 用 `send_input` 交付 handoff。
6. 等待 reviewer 只写 `review/result/reviewer_findings.raw.yaml`。
7. 运行 `./.qros/bin/qros-review` 完成 closure。
