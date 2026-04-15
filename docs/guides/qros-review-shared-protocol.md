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

## Adversarial Reviewer Contract

你是 `adversarial reviewer-agent`，不是原始 author。

在任何 closure artifacts 出现之前，必须先完成：

1. 检查 `adversarial_review_request.yaml`
2. 确认 reviewer identity 与 `author_identity` 不同
3. 对 `required_program_dir` 和 `required_program_entrypoint` 做 `source-code inspection`
4. 检查 request 中列出的必需 artifacts 与 provenance
5. 写出 `adversarial_review_result.yaml`

## Required Review Result Fields

`adversarial_review_result.yaml` 至少必须包含：

- `review_cycle_id`
- `reviewer_identity`
- `reviewer_role`
- `reviewer_session_id`
- `reviewer_mode: adversarial`
- `review_loop_outcome`
- `reviewed_program_dir`
- `reviewed_program_entrypoint`
- `reviewed_artifact_paths`
- `reviewed_provenance_paths`
- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`

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

只有结果达到 closure-ready，才运行 `./.qros/bin/qros-review`。

## Shared Verdict Vocabulary

- `PASS`
- `CONDITIONAL PASS`
- `PASS FOR RETRY`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`
