---
name: qros-csf-holdout-validation-review
description: Codex review skill for CSF Holdout Validation stage verification.
---

# CSF Holdout Validation Review

## Purpose

在最后完全未参与设计的窗口里验证冻结方案是否仍然稳定

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/review-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- 已冻结的 csf_backtest_ready 输出
- 最终 holdout 窗口
- regime shift 审计提案

## Required Outputs

Required outputs:
- csf_holdout_run_manifest.json
- holdout_factor_diagnostics.parquet
- holdout_test_compare.parquet
- holdout_portfolio_compare.parquet
- rolling_holdout_stability.json
- regime_shift_audit.json
- csf_holdout_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: CSF Holdout Validation

Formal gate summary:
Must pass all of:
- 只复用冻结方案，不重估上游尺子
- 主要方向未翻向
- 退化可解释且未超过容忍边界
- holdout 覆盖和 breadth 未塌到不可解释
- regime shift 明显时，必须显式审计
Must fail none of:
- 在 holdout 调参
- 在 holdout 改 bucket cut、neutralization、weight mapping
- 主要证据翻向
- 结果只靠极少数窗口支撑
- regime shift 明显却没有审计结论

## Checklist

Stage checklist:
- [blocking] holdout 只复用冻结方案，不重新调参或改写组合规则
- [blocking] holdout_factor_diagnostics 已记录 coverage、breadth、方向一致性和分桶稳定性
- [blocking] holdout_test_compare 与 holdout_portfolio_compare 已生成
- [blocking] regime_shift_audit 已明确记录是否存在显著结构迁移
- [blocking] 未在 holdout 中回写 train/test/backtest 的任何冻结对象
- [blocking] 若主要证据退化，已区分 regime mismatch、样本问题和机制断裂
- [reservation] 最终 holdout 结论、残留风险和后续 lineage 建议均已写明

## Audit-Only Items

Audit-only items:
- holdout 文字总结是否清楚
- regime shift 解释是否足够完整

## Closure Artifacts

- `latest_review_pack.yaml`
- `stage_gate_review.yaml`
- `stage_completion_certificate.yaml`

## Mandatory Adversarial Review Inputs

- `adversarial_review_request.yaml`
- lineage-local stage program source under the runtime-declared `required_program_dir`
- stage provenance in `program_execution_manifest.json`

## Mandatory Adversarial Reviewer Contract

You are the adversarial reviewer-agent lane, not the original author.

Before any closure artifacts can exist:

1. Inspect `adversarial_review_request.yaml`
2. Verify your reviewer identity differs from `author_identity`
3. Perform source-code inspection of the lineage-local stage program in `required_program_dir` and its `required_program_entrypoint`
4. Inspect the required artifacts and provenance named in the request
5. Write `adversarial_review_result.yaml`

`adversarial_review_result.yaml` must include at least:

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

Allowed `review_loop_outcome` values:

- `FIX_REQUIRED`
- `CLOSURE_READY_PASS`
- `CLOSURE_READY_CONDITIONAL_PASS`
- `CLOSURE_READY_PASS_FOR_RETRY`
- `CLOSURE_READY_RETRY`
- `CLOSURE_READY_NO_GO`
- `CLOSURE_READY_CHILD_LINEAGE`

`FIX_REQUIRED` means: return the stage to the author for fixes; do not allow closure artifacts.

The closure-ready adverse verdict path includes `CLOSURE_READY_NO_GO`, `CLOSURE_READY_CHILD_LINEAGE`, and any equivalent closure-ready terminal failure outcome; these may proceed to deterministic closure writing and downstream failure routing.

## Optional Reviewer Findings File

You may also create `review_findings.yaml` in the current `stage_dir` for human-readable detail and rollback metadata.

Minimum expected fields:

- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`
- `recommended_verdict`
- `rollback_stage`
- `allowed_modifications`

Use reviewer findings for semantic judgment. Let the review engine handle the hard evidence checks and final artifact writing.

## Allowed Verdicts

- `PASS`: 当前阶段目标已满足，无保留事项
- `CONDITIONAL PASS`: 当前阶段主要目标满足，但存在必须明示的保留事项
- `PASS FOR RETRY`: 允许按既定 rollback 范围受控重试，未完成前不得继续晋级
- `RETRY`: 当前阶段失败，但失败原因仍属于受控可修复问题
- `NO-GO`: 组织上不支持继续推进当前方案
- `GO`: 组织上批准进入下一治理或运行阶段
- `CHILD LINEAGE`: 需要以新谱系承接，不允许在原线静默改题
- `GO_TO_MANDATE`: 想法通过 qualification，允许进入 mandate_confirmation_pending 并申请生成 Mandate 产物
- `NEEDS_REFRAME`: 方向可研究，但当前边界或变量定义不足，需按 required_reframe_actions 重写后再审
- `DROP`: 不值得投入进一步研究预算，终止该想法

## Rollback Rules

- Default rollback stage: csf_holdout_validation
- Allowed modification: 澄清文档表述
- Allowed modification: 补全缺失 artifact
- Allowed modification: 修正 holdout 审计说明
- Must open child lineage when: holdout 表明研究语义已改变
- Must open child lineage when: regime shift 解释要求重设研究问题

## Downstream Permissions

- May advance to: promotion_decision
- Frozen output consumable by next stage: csf_holdout_gate_decision.md
- Frozen output consumable by next stage: regime_shift_audit.json
- Next stage must not consume/re-estimate: 未冻结的 holdout 调参结果

## Verdict Flow

1. Confirm current stage
2. Load the stage contract
3. Load the stage checklist
4. Check required inputs and outputs
5. Evaluate the formal gate first
6. Inspect the lineage-local source code for this stage
7. Record audit-only findings after that
8. Save `adversarial_review_result.yaml` and, if useful, `review_findings.yaml`
9. If outcome is `FIX_REQUIRED`, return to the author lane and stop before closure
10. Only if the outcome is closure-ready, run `~/.qros/bin/qros-review`
11. Review the generated closure artifacts
