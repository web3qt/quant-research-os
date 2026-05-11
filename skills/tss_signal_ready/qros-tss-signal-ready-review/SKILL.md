---
name: qros-tss-signal-ready-review
description: Use when a QROS time_series_signal lineage is ready for explicit tss_signal_ready review.
---

# TSS Signal Ready Review

## Runtime Stage Admission

开始本 stage-specific review 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage tss_signal_ready --lane review`

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
- `contracts/artifacts/tss_signal_ready_artifacts.yaml`
- `artifact_catalog.md`
- `field_dictionary.md`
- `run_manifest.json`

## 必需输入

- `02_tss_data_ready/review/closure/stage_completion_certificate.yaml`
- `03_tss_signal_ready/author/formal/signal_manifest.yaml`
- `03_tss_signal_ready/author/formal/param_manifest.csv`
- `03_tss_signal_ready/author/formal/signal_panel.parquet`
- `03_tss_signal_ready/author/formal/signal_event_panel.parquet`
- `03_tss_signal_ready/author/formal/route_inheritance_contract.yaml`

## 必需输出

- `review/result/reviewer_findings.raw.yaml`
- `review/result/adversarial_review_result.yaml`
- `review/result/review_findings.yaml`
- `review/closure/stage_completion_certificate.yaml`

## 正式门禁

- 进入 reviewer lane 前必须已经运行 `qros-validate-stage --stage tss_signal_ready`。
- 只能审查 `research_route = time_series_signal` 的 `03_tss_signal_ready` 产物。
- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

## 审查清单

- [blocking] signal schema、param identity、time semantics 已冻结且可复现。
- [blocking] signal panel 是单资产时间序列语义，不是横截面 ranking panel。
- [blocking] event panel 的 anchor/horizon/direction 无前视。
- [blocking] route inheritance 与 mandate、tss_data_ready 一致。
- [blocking] author outputs 非 placeholder，且 `artifact_catalog.md` / `field_dictionary.md` 覆盖实际字段。

## Rollback 规则

- 默认 rollback stage：`tss_signal_ready`。
- 允许修改：补全 artifact、修正字段文档、修复 stage program。
- 若改变核心信号机制、route、bar size 或 time split，必须回退到 mandate 或开 child lineage。

## 下游权限

- 通过 closure 后可进入 `tss_train_freeze_confirmation_pending`。
- 下游只允许消费已冻结的 signal schema、param manifest、signal/event panels。

## 执行顺序

1. 完成 review-ready 自查并确认 handoff scope 是当前 author outputs。
2. 运行 `qros-validate-stage --stage tss_signal_ready`。
3. 用 `spawn_agent` 创建独立 reviewer 子代理。
4. 运行 `./.qros/bin/qros-review-cycle prepare`。
5. 用 `send_input` 交付 handoff。
6. 等待 reviewer 只写 `review/result/reviewer_findings.raw.yaml`。
7. 运行 `./.qros/bin/qros-review` 完成 closure。
