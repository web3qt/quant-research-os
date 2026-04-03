---
name: qros-csf-signal-ready-review
description: Codex review skill for CSF Signal Ready stage verification.
---

# CSF Signal Ready Review

## Purpose

将已冻结的截面研究语义实例化为可比较、可复现的因子面板合同

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/review-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- 已冻结的 csf_data_ready 输出
- 因子表达式或多因子组合草案
- 因子方向与时间语义提案

## Required Outputs

Required outputs:
- factor_panel.parquet
- factor_manifest.yaml
- factor_field_dictionary.md
- factor_coverage_report.parquet
- factor_contract.md
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: CSF Signal Ready

Formal gate summary:
Must pass all of:
- factor_id / factor_version / factor_direction 已冻结
- factor_panel 可唯一表示同一时点不同资产的因子值
- 所有输入字段都来自 csf_data_ready
- 多因子组合公式是确定性的
- 缺失值、coverage、eligibility 传递规则已写清
- 因子方向明确，不允许到 test/backtest 再解释
Must fail none of:
- 因子定义依赖 train/test/backtest 结果回写
- factor_panel 无法稳定重建
- 多因子组合权重在后续阶段才学习
- factor_direction 不清楚
- eligibility 与 factor computation 混成一团
- test 才知道的 quantile / cutoff 被偷写回 signal

## Checklist

Stage checklist:
- [blocking] factor_role、factor_structure、portfolio_expression、neutralization_policy 均来自 mandate 冻结；non-standalone 具备 target_strategy_reference，group_neutral 具备 group_taxonomy_reference
- [blocking] factor_id、factor_version、factor_direction 已冻结
- [blocking] factor_panel 以统一面板主键唯一表示同一时点不同资产的因子值
- [blocking] raw_factor_fields、derived_factor_fields 和 final_score_field 已写清
- [blocking] 多因子组合公式是确定性的，不依赖 train-learned weights
- [blocking] 缺失值策略、coverage contract 和 eligibility 传递规则已冻结
- [blocking] 若需要组内排序或组中性化，factor group context 已冻结
- [blocking] 不得把过滤器语义伪装成独立 alpha 语义

## Audit-Only Items

Audit-only items:
- 因子命名是否足够可读
- 多因子组合描述是否清楚

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

- Default rollback stage: csf_signal_ready
- Allowed modification: 澄清文档表述
- Allowed modification: 补全缺失 artifact
- Allowed modification: 修正因子方向与组合公式
- Must open child lineage when: 因子结构从截面改为时序
- Must open child lineage when: 因子角色发生实质变化

## Downstream Permissions

- May advance to: csf_train_freeze
- Frozen output consumable by next stage: factor_panel.parquet
- Frozen output consumable by next stage: factor_manifest.yaml
- Frozen output consumable by next stage: factor_coverage_report.parquet
- Next stage must not consume/re-estimate: 未冻结的 train 尺子

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
