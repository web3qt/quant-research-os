# QROS Shared Review Protocol

## Purpose

这个文档承载所有 stage review skill 共用的审查协议，避免每个 review skill 重复内联同一套 boilerplate。

各阶段 `qros-*-review` skill 只保留 stage-specific 的 formal gate、checklist、audit-only、rollback 和 downstream 规则；共享审查纪律统一以本文件为准。

## Shared Inputs

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Closure Artifacts

- `review/closure/latest_review_pack.yaml`
- `review/closure/stage_gate_review.yaml`
- `review/closure/stage_completion_certificate.yaml`

## Review Trace

为方便按 `session / reviewer / review_cycle_id` 做 postmortem，当前 review lane 还会把关键节点追加到：

- `review/review_cycle_trace.jsonl`

它至少会记录：

- request issued
- spawned reviewer receipt issued
- reviewer write-scope audit completed
- review evaluated（`FIX_REQUIRED` 或 closure-ready verdict）

## Leader / Launcher Discipline

发起 review 的当前主线程必须实际启动一个独立 reviewer 子代理。

- `spawned_agent` 在本协议里指真实独立的 child agent / subagent，不是把 reviewer identity 改掉后继续在当前线程审查
- 在当前 `Codex-only` 版本里，这个 child agent 必须通过 native `spawn_agent` 启动
- 当前主线程只允许准备 `review/request/*`、写 launcher-side receipt、等待 reviewer 子代理落 `review/result/*`，以及在 closure-ready 后运行 `./.qros/bin/qros-review`
- 当前主线程在运行 `./.qros/bin/qros-review` 之前，必须先运行 deterministic reviewer write-scope audit，并确认 `review/result/reviewer_write_scope_audit.yaml` 为 `PASS`
- 当前主线程不得自己撰写 `review/result/adversarial_review_result.yaml` 或 `review/result/review_findings.yaml`
- 若 reviewer 子代理未成功启动，只能保持 review pending / launch blocked，不得 fallback 到同线程 review

## Launcher Review-Ready / Repair Loop

review 不应该把 reviewer 当成“第一轮帮 author 补交作业”的入口。

在启动 reviewer 子代理之前，launcher / 主 Agent 必须先完成一次 `review-ready` 自查，至少包括：

- 重新核对当前 stage contract、author skill 要求和 active request scope
- 确认 `author/formal/*` 中已经有当前 stage 要求的 formal artifacts、`artifact_catalog.md`、`field_dictionary.md`、`run_manifest.json` 和当前 stage program provenance
- 确认 machine-readable artifacts 不是 placeholder / contract-only stub，而是当前可读取、可审计的真实最小产物
- 确认 `adversarial_review_request.yaml` 指向的是**当前** author outputs，而不是旧路径、旧 digest 或上一轮修复前的 stale scope
- 给 reviewer 一个明确 handoff：当前声称已完成的 outputs、这轮希望 reviewer 验证的 formal gate、已知限制 / 未决假设 / 需要重点盯的风险

这层 handoff 现在还必须冻结成 request / manifest 字段，而不是只留在聊天里：

- `launcher_review_ready_status: complete`
- `launcher_checked_artifact_paths`
- `launcher_checked_provenance_paths`
- `launcher_handoff_context_paths`

如果当前 review cycle 返回 `FIX_REQUIRED`，launcher / 主 Agent 必须：

- 先阅读 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`
- 回到 author lane，只在允许的修改边界内修复 findings，不得让 reviewer 直接改原产物
- 修复后刷新 `author/formal/*` 与 request scope，再发起新的 reviewer cycle
- author outputs 一旦变化，就不得继续复用旧的 receipt / result / audit 作为新一轮 proof
- 同一 active review cycle 只允许一个 reviewer child；旧 cycle 未解决前，不得再并发启动第二个 reviewer child

## Adversarial Reviewer Contract

你是 `adversarial reviewer-agent`，不是原始 author。

在任何 closure artifacts 出现之前，必须先完成：

1. 检查 `adversarial_review_request.yaml`
2. 确认 `spawned_reviewer_receipt.yaml` 已由 runtime launcher 写出
3. 确认 reviewer identity 与 `author_identity` 不同
4. 对 `required_program_dir` 和 `required_program_entrypoint` 做 `source-code inspection`
5. 检查 request 中列出的必需 artifacts 与 provenance
6. 写出 `adversarial_review_result.yaml`

`./.qros/bin/qros-review` 运行时只会以 active request 为准，规范化
program scope 和 reviewed artifact scope。
它不会替你补写 `spawned_reviewer_receipt.yaml`，也不会回填
`reviewer_execution_mode`、`reviewer_context_source`、
`reviewer_history_inheritance`、`handoff_manifest_digest`、`review_cycle_id`、
reviewer identity / session 等 proof 或 binding 字段。
不要把磁盘上已有的 `adversarial_review_result.yaml` 当作不可质疑真值。

`adversarial_review_request.yaml` 与 handoff manifest 当前都必须带上同一套
launcher `review-ready` 字段。只要 launcher 修过 `author/formal/*` 却没刷新这些字段，
proof chain 就必须失效。

## Spawned Reviewer Receipt

当前唯一允许的 reviewer 形态是 `spawned_agent`，也就是独立 reviewer 子代理。

在 reviewer 写 `review/result/*` 之前，runtime launcher 必须先写出：

- `review/request/spawned_reviewer_receipt.yaml`

它至少要证明：

- `spawn_mode: spawned_agent`
- `launcher_thread_id`
- `spawned_agent_id`
- `fork_context: false`
- `write_root: review/result`
- `requested_reviewer_identity`
- `requested_reviewer_session_id`
- `handoff_manifest_path`
- `handoff_manifest_digest`

`spawned_reviewer_receipt.yaml` 是 launcher-side proof，不是当前主线程可继续自审的许可证。

launch receipt 写出时，还必须同时冻结 reviewer write-scope baseline：

- `review/request/reviewer_write_scope_baseline.yaml`

reviewer 的输入来源也必须被 request/receipt/result 三段一致地限制在：

- `review/request/*`
- `author/formal/*`

但当前 review request 现在会再把 scope 拆成三层：

- `required_artifact_paths` / `required_provenance_paths`
  这是当前 stage 完整 formal package 与 provenance 的 deterministic gate scope
- `stage_content_artifact_paths` / `stage_content_provenance_paths`
  这是 reviewer 子代理真正负责的 stage-local 内容审查范围
- `upstream_binding_artifact_paths` / `upstream_binding_provenance_paths`
  这是 deterministic upstream binding validator 负责的上游绑定范围，不属于 reviewer 的自由发挥范围

对应的 handoff manifest 还必须明确：

- `launcher_review_ready_status: complete`
- `launcher_checked_artifact_paths` 必须覆盖 active request 的全部 required artifacts
- `launcher_checked_provenance_paths` 必须覆盖 active request 的全部 required provenance
- `launcher_handoff_context_paths` 必须与当前 required context files 一致

## Required Review Result Fields

`adversarial_review_result.yaml` 至少必须包含：

- `review_cycle_id`
- `reviewer_identity`
- `reviewer_role`
- `reviewer_session_id`
- `reviewer_mode: adversarial`
- `reviewer_agent_id`
- `reviewer_execution_mode: spawned_agent`
- `reviewer_context_source: explicit_handoff_only`
- `reviewer_history_inheritance: none`
- `handoff_manifest_digest`
- `review_loop_outcome`
- `reviewed_program_dir`
- `reviewed_program_entrypoint`
- `reviewed_artifact_paths`
- `reviewed_provenance_paths`
- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`

当前 runtime 允许 reviewer 先写一个更窄的原始结果：

- `review/result/reviewer_findings.raw.yaml`

若该文件存在而正式 `adversarial_review_result.yaml` 尚未落盘，runtime 会按 active request / receipt / runtime reviewer identity 做 deterministic 规范化写入。  
也就是说，reviewer 不再需要手写所有 proof / binding 字段；这些字段以 runtime 真值为准。

在进入 closure 前，当前 review cycle 还必须额外产出：

- `review/result/reviewer_write_scope_audit.yaml`

它至少要证明：

- `review_cycle_id`
- `launcher_thread_id`
- `spawned_agent_id`
- `audit_status: PASS`
- protected files 没有被 reviewer 越权修改
- `review/result/*` 之外没有 reviewer 写入

## Review Loop Outcomes

允许的 `review_loop_outcome`：

- `FIX_REQUIRED`
- `CLOSURE_READY_PASS`
- `CLOSURE_READY_CONDITIONAL_PASS`
- `CLOSURE_READY_PASS_FOR_RETRY`
- `CLOSURE_READY_RETRY`
- `CLOSURE_READY_NO_GO`
- `CLOSURE_READY_CHILD_LINEAGE`

`FIX_REQUIRED` 表示退回 author 修复；不得允许 closure artifacts 出现。

`closure-ready adverse verdict` 路径包括 `CLOSURE_READY_NO_GO`、`CLOSURE_READY_CHILD_LINEAGE`，以及其它等价的 closure-ready terminal failure outcome。

## Optional Human-Facing Findings

如有必要，可额外写 `review_findings.yaml`，最低建议字段：

- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`
- `recommended_verdict`
- `rollback_stage`
- `allowed_modifications`

## Execution Gate

只有结果达到 closure-ready，且 `reviewer_write_scope_audit.yaml` 为 `PASS`，才运行 `./.qros/bin/qros-review`。

如果 `spawned_reviewer_receipt.yaml` 缺失、request/receipt/result 的
`review_cycle_id` 或 `handoff_manifest_digest` 不一致、receipt 中指定的
reviewer 与真正提交 result 的 reviewer 不一致，`qros-review` 必须直接失败。

如果 request / handoff manifest 的 `review-ready` 字段不完整，或者 launcher
声称检查过的 paths 与 active request scope 不一致，`qros-review` 也必须直接失败。

在真正 spawn reviewer 之前，建议先运行：

- `./runtime/bin/qros-review-preflight`

它会先做 deterministic 的 stage content / upstream binding 预检；只有预检通过，才值得进入 reviewer lane。

`review/review_cycle_trace.jsonl` 不参与 gate 判定，但应保持可追加、可搜索，方便未来按 session id、reviewer session、spawned agent id 或 review_cycle_id 还原一次 review cycle。

对 `csf_test_evidence`、`csf_backtest_ready`、`csf_holdout_validation` 这三类
CSF stage，`qros-review` 不只检查 artifact 是否存在，还会读取关键数值门禁：

- `standalone_alpha` 的 `mean_rank_ic` 必须为正
- `csf_backtest_ready` 的 `mean_net_return` 必须为正
- `csf_holdout_validation` 的 `direction_match` 必须为 `true`，且 `holdout_mean_net_return` 必须为正

这些 hard metric gates 触发时，必须写成 `blocking_findings`，不得因为 artifact 齐全就给 `PASS`。

对前半段 `csf_data_ready`、`csf_signal_ready`、`csf_train_freeze`，严格性来自
合同/语义 gate，而不是收益门：

- `csf_data_ready` 必须冻结非空的 panel key 与 shared feature base 合同
- `csf_data_ready` 的 `cross_section_coverage.parquet` 还必须满足冻结的 coverage floor 数值门
- `csf_signal_ready` 必须冻结合法的 `factor_direction`、panel key 和 score 字段
- `csf_train_freeze` 必须冻结非空的 candidate / kept variants 与 train-governable axes
- `csf_train_freeze` 的 `train_factor_quality.parquet` 不能是空表，`train_variant_ledger.csv` 的 `variant_id` 不得重复

这些 contract gates 触发时，同样必须写成 `blocking_findings`，不能用“后面 test/backtest 再看”来放行。

当 stage contract 额外挂了 `row_count_gt` 或 `unique_key` 时，review 还会检查：

- 对应 parquet / csv 不是空表
- 约定主键（例如 `date × asset`）没有重复

因此，runtime builder 不能再把 `.parquet` 产物写成占位文本；至少要生成可被正常读取的最小真实表。

对 `csf_signal_ready`，最小真实表还应优先从 `csf_data_ready` 的 membership / eligibility / taxonomy / shared feature base 派生，而不是静态硬编码资产集合。

## Shared Verdict Vocabulary

- `PASS`
- `CONDITIONAL PASS`
- `PASS FOR RETRY`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`
