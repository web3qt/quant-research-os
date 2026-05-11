---
name: qros-tss-data-ready-review
description: Use when a QROS time_series_signal lineage is ready for explicit tss_data_ready review.
---

# TSS Data Ready Review

## Runtime Stage Admission

开始本 stage-specific review 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage tss_data_ready --lane review`

若命令失败，必须停止；不得继续 review，不得启动 reviewer，不得运行 `qros-review-cycle prepare`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

只有 `qros-review` deterministic closer 可以写 canonical result、audit 与 closure；普通 reviewer findings 不能替代 closure。

## 独立 reviewer 子代理要求

- 进入本 skill 后，必须在当前会话中用 `spawn_agent` 拉起独立 reviewer 子代理，且 `fork_context` 必须是 `false`。
- reviewer 子代理创建后，主线程优先运行 `./.qros/bin/qros-review-cycle prepare` 注册 active review cycle 并写出 `review/request/*`。
- 主线程用 `send_input` 交付 request / handoff / 本 stage formal gate。
- reviewer 子代理只允许读取 `review/request/*` 与 `author/formal/*`。
- reviewer 子代理只允许写入 `review/result/reviewer_findings.raw.yaml`。
- reviewer 子代理不得修改 author/formal。
- reviewer 完成后，主线程必须运行 `./.qros/bin/qros-review` 完成 closure。

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
- `contracts/artifacts/tss_data_ready_artifacts.yaml`
- `artifact_catalog.md`
- `field_dictionary.md`
- `run_manifest.json`

## 必需输入

- `01_mandate/review/closure/stage_completion_certificate.yaml`
- `02_tss_data_ready/author/formal/time_index_manifest.json`
- `02_tss_data_ready/author/formal/asset_time_index.parquet`
- `02_tss_data_ready/author/formal/quality_flags.parquet`
- `02_tss_data_ready/author/formal/split_sample_adequacy_report.yaml`

## 必需输出

- `review/result/reviewer_findings.raw.yaml`
- `review/result/adversarial_review_result.yaml`
- `review/result/review_findings.yaml`
- `review/closure/stage_completion_certificate.yaml`

## 正式门禁

- 进入 reviewer lane 前必须已经运行 `qros-validate-stage --stage tss_data_ready`。
- 只能审查 `research_route = time_series_signal` 的 `02_tss_data_ready` 产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。
- 不得产出或消费 `csf_*` 横截面因子产物。

## 审查清单

- [blocking] `asset_time_index.parquet` 是单资产或逐资产时间轴，而不是横截面排名面板。
- [blocking] quality flags 与缺失语义可被下游稳定消费。
- [blocking] split sample adequacy 覆盖 train/test/backtest/holdout。
- [blocking] `artifact_catalog.md` 与 `field_dictionary.md` 覆盖 machine-readable artifacts。
- [blocking] author outputs 非 placeholder，且 provenance 可重放。

## Rollback 规则

- 默认 rollback stage：`tss_data_ready`。
- 允许修改：补全缺失 artifact、修正质量语义说明、修复 stage program。
- 若需要改 mandate 的 route、universe、bar size 或 time split，必须回退到 mandate 或开 child lineage。

## 下游权限

- 通过 closure 后可进入 `tss_signal_ready_confirmation_pending`。
- 下游只能消费 `02_tss_data_ready/author/formal` 与 review closure。

## 执行顺序

1. 完成 review-ready 自查并确认 handoff scope 是当前 author outputs。
2. 运行 `qros-validate-stage --stage tss_data_ready`。
3. 用 `spawn_agent` 创建独立 reviewer 子代理。
4. 运行 `./.qros/bin/qros-review-cycle prepare`。
5. 用 `send_input` 交付 handoff。
6. 等待 reviewer 只写 `review/result/reviewer_findings.raw.yaml`。
7. 运行 `./.qros/bin/qros-review` 完成 closure。
