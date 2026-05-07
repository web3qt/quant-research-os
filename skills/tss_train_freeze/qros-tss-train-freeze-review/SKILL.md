---
name: qros-tss-train-freeze-review
description: Use when a QROS time_series_signal lineage is ready for explicit tss_train_freeze review.
---

# TSS Train Freeze Review

## Runtime Stage Admission

开始本 stage-specific review 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage tss_train_freeze --lane review`

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

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/artifacts/tss_train_freeze_artifacts.yaml`
- `artifact_catalog.md`
- `field_dictionary.md`
- `run_manifest.json`

## 必需输入

- `03_tss_signal_ready/review/closure/stage_completion_certificate.yaml`
- `04_tss_train_freeze/author/formal/tss_train_freeze.yaml`
- `04_tss_train_freeze/author/formal/train_threshold_ledger.csv`
- `04_tss_train_freeze/author/formal/train_variant_ledger.csv`
- `04_tss_train_freeze/author/formal/train_variant_rejects.csv`

## 必需输出

- `review/result/reviewer_findings.raw.yaml`
- `review/result/adversarial_review_result.yaml`
- `review/result/review_findings.yaml`
- `review/closure/stage_completion_certificate.yaml`

## 正式门禁

- 进入 reviewer lane 前必须已经运行 `qros-validate-stage --stage tss_train_freeze`。
- 只能审查 `research_route = time_series_signal` 的 `04_tss_train_freeze` 产物。
- 不得产出或消费 `csf_*` 横截面因子产物。
- 不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

## 审查清单

- [blocking] 阈值和过滤只来自 train window，没有读取未来窗口。
- [blocking] 所有 variant 来自已冻结 `param_manifest.csv`。
- [blocking] reject ledger 保留失败与排除原因。
- [blocking] 没有收益最大化选最终参数或回写机制定义。
- [blocking] author outputs 非 placeholder，且 provenance 可重放。

## Rollback 规则

- 默认 rollback stage：`tss_train_freeze`。
- 允许修改：补全 ledger、修正阈值记录、修复 stage program。
- 若需改变信号 schema 或新增未冻结 param_id，必须回退到 `tss_signal_ready` 或开 child lineage。

## 下游权限

- 通过 closure 后可进入 `tss_test_evidence_confirmation_pending`。
- 下游只允许消费冻结阈值、variant ledger 和 reject ledger。

## 执行顺序

1. 完成 review-ready 自查并确认 handoff scope 是当前 author outputs。
2. 运行 `qros-validate-stage --stage tss_train_freeze`。
3. 用 `spawn_agent` 创建独立 reviewer 子代理。
4. 运行 `./.qros/bin/qros-review-cycle prepare`。
5. 用 `send_input` 交付 handoff。
6. 等待 reviewer 只写 `review/result/reviewer_findings.raw.yaml`。
7. 运行 `./.qros/bin/qros-review` 完成 closure。
