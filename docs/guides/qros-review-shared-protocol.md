# QROS 共享 Review 协议

## 目的

这个文档承载所有 stage review skill 共用的审查协议，避免每个 review skill 重复内联同一套 boilerplate。

各阶段 `qros-*-review` skill 只保留 stage-specific 的 formal gate、checklist、audit-only、rollback 和 downstream 规则；共享审查纪律统一以本文件为准。

当前生成的 review skills 是 workflow entrypoints，不是 stage truth source。stage-specific gates、outputs、checklist、rollback 和 downstream permissions 应通过当前 review cycle 生成的 contract context 文件读取，而不是从 skill 正文手抄或复述。

## 共享输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Review Contract Context

`qros-review-cycle prepare` 现在还会写出：

- `review/request/stage_contract_context.yaml`
- `review/request/stage_contract_context.md`

这两份文件是 current contracts 与 current author outputs 的 review-cycle-local rendering。reviewer 应以它们作为当前 stage truth 的入口，而不是从生成 skill 正文重建 formal gate。

换句话说，它们是 review-cycle-local rendering of current contracts and current author outputs。

## Closure Artifacts / 关闭产物

- `review/closure/latest_review_pack.yaml`
- `review/closure/stage_gate_review.yaml`
- `review/closure/stage_completion_certificate.yaml`

## Review Trace / 审查轨迹

为方便按 `session / reviewer / review_cycle_id` 做 postmortem，review lane 继续把关键节点追加到：

- `review/review_cycle_trace.jsonl`

它至少会记录：

- request issued
- reviewer handoff issued
- reviewer write-scope audit completed
- review evaluated

## Launcher / Reviewer 职责纪律

review 必须由**人显式确认**。普通路径中的显式动作由 `qros-research-session` 询问并记录 `CONFIRM_REVIEW`；stage-specific `qros-*-review` skill 只作为高级/debug/manual recovery 入口，或由 `qros-research-session` 在当前 stage 已匹配时内部复用。

只有 canonical review-eligible 的 stage 才允许进入 review lane。hard gate fail、deterministic preflight fail、failure package 已接管，或已经处于 `FAILURE_DISPOSITION_REQUIRED` / `FAILURE_DISPOSITION_RECORDED` 的 stage，都不是 ordinary review-lane candidate；`review_confirmation_pending` 不能被当作“artifact 齐了就默认进入 review”的通用槽位。若当前 runtime 仍把 `current_stage` 投影成 `*_review_confirmation_pending`，但同时用 `stage_status` / `blocking_reason_code` 标明 blocked，应以后者为准，把它当作 blocked stage，而不是 review-ready 证明。

当前 rollout 里，`mandate_review_confirmation_pending`、`data_ready_review_confirmation_pending`、`csf_data_ready_review_confirmation_pending` 和 `tss_data_ready_review_confirmation_pending` 已强制接入 deterministic review-entry preflight。这道 preflight 会先做 artifact contract validation、stage semantic validation、stage program provenance、thin wrapper program gate、placeholder / fake machine artifact gate，并继续覆盖已接入的 upstream research / binding blocker。例如 mandate 冻结窗口超出真实数据覆盖时，`review_preflight` 必须直接返回 `FAIL` payload，并把 blocker 暴露为 `research_preflight_findings`；同时它也必须落到现有 findings 通道，避免旧 launcher/聚合方看到一个没有原因的 fail。reviewer lane 不负责把这类已知 blocker 再做成第一轮发现式审查。

不过这条 blocker 不得盖过 protected review-state drift。只要 `REVIEW_STATE_PROJECTION_DRIFT` 存在，shared preflight 仍必须先按 drift fail-closed，而不是先回 research blocker。

- author lane 只负责 freeze / build / author fix
- review lane 由当前 `qros-research-session` 主线程承担 launcher 角色；高级/debug 入口下也可以由当前 stage-specific review skill 所在主线程承担
- launcher 主线程必须通过 host 特定的 reviewer 启动机制拉起独立 reviewer 子代理（Codex 下为 `spawn_agent`，Claude Code 下通过独立 reviewer agent task 创建），不能自己冒充 reviewer judgement
- launcher 主线程不得自己撰写 `review/final_review.yaml`
- launcher 主线程不得直接写 closure artifacts
- reviewer 子代理不得修改 `author/formal/*`
- reviewer 子代理正常只写 `review/final_review.yaml`
- ordinary final review 是 strict receipt-bound；`review/final_review.yaml` 单独存在不构成 closure proof
- active `reviewer_receipt.yaml` 必须绑定 reviewer identity、reviewer session、execution / agent identity、active request scope、author materialization digest 与 review context
- 主线程 / runtime 在 reviewer 完成后读取 `review/final_review.yaml`，先校验 receipt、normalized scope、author digest freshness 与 final review normalization；随后投影 `review/result/adversarial_review_result.yaml` 并运行 reviewer write-scope audit；audit 通过后才可写 closure artifacts 或推进 author-fix、next-stage confirmation / failure handling
- 对于当前 review-entry preflight rollout 已接入的 artifact contract validation、stage semantic validation、stage program provenance 与 research/upstream binding blocker，launcher 必须在 reviewer 启动前就停下；不得把这类 blocker 重新包装成 reviewer 的第一轮发现任务

## Launcher Review-Ready / 修复循环

review 不应该把 reviewer 当成“第一轮帮 author 补交作业”的入口。

在启动 reviewer 子代理之前，launcher 主线程必须先完成一次 `review-ready` 自查，必须包括：

- 重新核对当前 stage contract、author skill 要求和 active request scope
- 确认 `author/formal/*` 中已经有当前 stage 要求的 formal artifacts、`artifact_catalog.md`、`field_dictionary.md`、`run_manifest.json` 和当前 stage program provenance
- 确认 machine-readable artifacts 不是 placeholder / contract-only stub，而是当前可读取、可审计的真实最小产物；这一步是必须完成的硬门禁，不是建议项
- 确认 handoff 指向的是**当前** author outputs，而不是旧路径、旧 digest 或上一轮修复前的 stale scope
- 给独立 reviewer 子代理一个明确 handoff：当前声称已完成的 outputs、这轮希望 reviewer 验证的 formal gate、已知限制 / 未决假设 / 需要重点盯的风险

这层 handoff 仍然必须冻结成 request / manifest 字段，而不是只留在聊天里：

- `launcher_review_ready_status: complete`
- `launcher_checked_artifact_paths`
- `launcher_checked_provenance_paths`
- `launcher_handoff_context_paths`

此外，launcher 必须把 `review/request/stage_contract_context.yaml` 与 `review/request/stage_contract_context.md` 一并交给 reviewer。

## Review Operations Recovery

Review recovery follows stable operations:

- `AUTHOR_FIX_REQUIRED_BEFORE_REVIEW`: deterministic review-ready preflight failed; do not launch reviewer.
- `REQUEST_REFRESH_REQUIRED`: active request or stage contract context no longer proves current author outputs.
- `FINAL_REVIEW_REWRITE_REQUIRED`: raw `review/final_review.yaml` cannot be accepted as written, usually due to scope or format mismatch.
- `REVIEWER_RESTART_REQUIRED`: the current reviewer cycle is invalid; do not reuse the old verdict.
- `FAILURE_HANDLING_REQUIRED`: verdict or failure package routes the lineage to formal failure handling.

Launcher agents must not convert these operations into informal judgment. They must follow the operation-specific recovery path.

## Adversarial Reviewer 合同

你是独立 reviewer 子代理中的 `adversarial reviewer-agent`，不是原始 author。

在任何 closure artifacts 出现之前，必须先完成：

1. 检查 active review request
2. 确认 reviewer identity 与 `author_identity` 不同
3. 对 `required_program_dir` 和 `required_program_entrypoint` 做 source-code inspection
4. 检查 request 中列出的必需 artifacts 与 provenance
5. 先读取 `review/request/stage_contract_context.yaml` 与 `review/request/stage_contract_context.md`
6. 只基于当前 handoff 与 `author/formal/*` 做审查
7. 正常只写出 `review/final_review.yaml`

不要把磁盘上已有的旧 review 结果当作不可质疑真值。只要 launcher 修过 `author/formal/*` 却没刷新 handoff 字段，proof chain 就必须失效。

## Final Review 必填字段

`review/final_review.yaml` 至少必须包含：

- `lineage_id`
- `stage_id`
- `reviewer_identity`
- `reviewer_agent_id`
- `reviewed_artifact_paths`
- `reviewed_program_path`
- `reviewed_artifact_digest`
- `reviewed_program_digest`
- `verdict`
- `review_summary`
- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`
- `allowed_modifications`
- `rollback_stage`
- `downstream_permissions`
- `recommended_next_action`

## Fail-Closed 边界码

下列边界码仍然是共享 review 协议的一部分；如果 proof chain、review scope 或 hard gate 语义被破坏，runtime / reviewer 必须 fail-closed，而不是静默继续：

- `REVIEWER_IDENTITY_COLLISION`
- `REVIEW_CONTEXT_ROOT_MISMATCH`
- `HARD_GATE_DOWNGRADED`
- `REVIEW_RESULT_PROJECTION_DRIFT`

## Lineage Immutable Ledger / 已冻结事实不可变账本

reviewer write-scope audit 只回答当前 review cycle 里的 reviewer 是否越权写入当前 stage 文件；它不负责证明上游 stage 的 formal facts 是否仍然等于 review closure 时的版本。

上游不可变性由 lineage 级账本负责：

- `<lineage_root>/lineage_lock_ledger.yaml`

当某个 stage 产生 PASS-like review closure 后，runtime 会锁定该 stage 的 formal artifacts、required provenance 和 `review/closure/*` digest。后续会话与进度入口都必须先校验该账本。

若已锁文件被修改或删除，runtime 必须用稳定 reason code 阻断：

- `FROZEN_ARTIFACT_MUTATED`

该阻断不是自动 child lineage。默认恢复动作是把被改文件恢复到已锁版本；只有用户明确要保留已冻结事实变更时，才新开 child lineage。

## Shared Verdict 语义

- `PASS` / `CONDITIONAL PASS`：允许进入 next-stage confirmation
- `FIX_REQUIRED`：退回 author-fix；不得继续普通下一阶段推进
- `RETRY` / `NO-GO` / `CHILD LINEAGE`：转入对应治理路径，而不是回普通 author lane 假装重试

`CHILD LINEAGE` 仍然只是 formal failure/disposition 结果。它不能被当成 review lane 的普通分支、不能替代 author-fix，也不能在没有 failure package / disposition 记录的情况下被非正式触发。

## 共享 Verdict 词表

- `PASS`
- `CONDITIONAL PASS`
- `FIX_REQUIRED`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`
