---
name: qros-tss-holdout-validation-review
description: Codex review skill for TSS Holdout Validation stage verification.
---

# TSS Holdout Validation 审查

## 用途

在 holdout 中复用冻结时序信号、交易规则和风险约束，审计最终退化和漂移

## Runtime Stage Admission

开始本 stage-specific review 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage tss_holdout_validation --lane review`

若命令失败，必须停止；不得继续 review，不得启动 reviewer，不得运行 `qros-review-cycle prepare`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

该共享审查协议统一定义：

- adversarial reviewer-agent 合同
- `adversarial_review_request.yaml` / `review/final_review.yaml` / closure artifacts 要求
- `FIX_REQUIRED` 与 closure-ready final verdict 语义
- reviewer 与 launcher 主线程的职责边界

## 独立 reviewer 子代理要求

- 本 skill 是用户显式进入的 stage-specific review 入口；不再要求你手动再开一个独立 review session
- 进入本 skill 后，必须在**当前会话**里用 `spawn_agent` 拉起独立 reviewer 子代理，且 `fork_context` 必须是 `false`
- 先用一个最小初始化消息创建 reviewer 子代理，要求它先等待 binding / handoff，不要在 receipt 写出前擅自写文件
- reviewer 子代理创建后，主线程优先运行 `./.qros/bin/qros-review-cycle prepare --reviewer-agent-id <child_agent_id> --reviewer-id <reviewer_identity> --reviewer-session-id <child_agent_id> --host codex`
- `qros-review-cycle prepare` 负责注册 active review cycle，写出 `review/request/*` 与 `reviewer_receipt.yaml`，并输出 reviewer handoff prompt
- 主线程随后必须用 `send_input` 把 request / handoff manifest / `stage_contract_context.yaml` / `stage_contract_context.md` 交给 reviewer 子代理
- reviewer 子代理只允许读取 `review/request/*` 与 `author/formal/*`
- reviewer 子代理只允许写入 `review/final_review.yaml`
- reviewer 子代理不得修改 `author/formal/*`
- reviewer 子代理完成后，主线程读取 `review/final_review.yaml` 并按 verdict 推进 author-fix、next-stage confirmation 或 failure handling

reviewer 写出的 `review/final_review.yaml` 必须包含以下顶层字段：

- `lineage_id`
- `stage_id`
- `reviewer_identity`
- `reviewer_agent_id`
- `reviewed_artifact_paths`
- `reviewed_program_path`
- `reviewed_artifact_digest`
- `reviewed_program_digest`
- `verdict: one of PASS, CONDITIONAL PASS, FIX_REQUIRED, RETRY, NO-GO, CHILD LINEAGE`
- `review_summary`
- `blocking_findings: []`
- `reservation_findings: []`
- `info_findings: []`
- `residual_risks: []`
- `allowed_modifications: []`
- `rollback_stage`
- `downstream_permissions: []`
- `recommended_next_action`

## 主线程交接前提

- 主线程在发起 review 之前必须先完成 `review-ready` 自查，不要把 reviewer 当成第一轮 artifact completeness checker
- 主线程交给 reviewer 子代理的 scope 必须是**当前** author outputs，而不是旧 request、旧 digest 或修复前的 stale artifacts
- handoff 必须明确这轮声称已完成的 outputs、希望 reviewer 验证的 formal gate、已知限制 / 未决假设，而不是盲交 reviewer
- handoff 必须与 `launcher_review_ready_status`、`launcher_checked_artifact_paths`、`launcher_checked_provenance_paths`、`launcher_handoff_context_paths` 一致
- 如果上一轮 `review/final_review.yaml` 的 verdict 是 `FIX_REQUIRED`，主线程必须先读取 `review/final_review.yaml`，只在 author lane 修复，再显式重新进入本 stage review skill
- 如果你发现 handoff scope 过期、必需输出缺失、machine-readable artifacts 只是 placeholder，应该明确写成 blocking findings / `FIX_REQUIRED`，而不是替主线程猜测或补齐上下文
- reviewer 不替 runtime 重定义字段；artifact shape 以 `contracts/artifacts/tss_holdout_validation_artifacts.yaml` 与 deterministic preflight 为准
- 进入 reviewer lane 前必须已经运行 `qros-validate-stage --stage tss_holdout_validation`，并通过 deterministic preflight
- preflight 中的 `ARTIFACT-CONTRACT-001` 与 `TSS-HOLDOUT-SEMANTIC-001` 都是 review 前阻断项
- preflight 覆盖 artifact contract validation、semantic validation 与 upstream binding validation；reviewer 仍需审查机制和残留风险

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Stage Contract Context

Do not reconstruct stage gates from memory or from this skill.
Run `./.qros/bin/qros-review-cycle prepare ...` and use:

- `review/request/stage_contract_context.yaml`
- `review/request/stage_contract_context.md`

These files are the review-cycle-local rendering of current contracts and current author outputs.

## 执行顺序

1. 在当前会话中完成 `review-ready` 自查，并确认 handoff 与 launcher 字段一致
2. 用 `spawn_agent` 创建独立 reviewer 子代理
3. 运行 `./.qros/bin/qros-review-cycle prepare` 写出 active request / handoff / receipt，并复用输出的 reviewer handoff prompt
4. 用 `send_input` 向 reviewer 子代理交付 request / handoff 与 `stage_contract_context.*`
5. 等待 reviewer 子代理只写 `review/final_review.yaml`
6. 主线程读取 `review/final_review.yaml`
7. 以 `stage_contract_context.*`、request scope 和 final verdict 解释当前 stage 的 review 结果，并交回 runtime/session 继续 author-fix、failure handling、next-stage confirmation 或 deterministic closure
