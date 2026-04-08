---
name: qros-csf-test-evidence-review
description: Codex review skill for CSF Test Evidence stage verification.
---

# CSF Test Evidence Review

## Purpose

在独立样本里验证截面因子排序能力或 filter / combo 条件改善能力

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/review-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- 已冻结的 csf_train_freeze 输出
- 独立测试窗
- factor_role / target_strategy_reference

## Required Outputs

Required outputs:
- csf_test_gate_table.csv
- csf_selected_variants_test.csv
- csf_test_contract.md
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: CSF Test Evidence

Formal gate summary:
Must pass all of:
- 只复用 csf_train_freeze 的 frozen rules
- `standalone_alpha` 使用 Rank IC / ICIR / bucket spread / monotonicity / breadth / stability
- `regime_filter / combo_filter` 使用 gated vs ungated 改善证据
- 全量 test ledger 保留
- selected / rejected variants 有显式记账
Must fail none of:
- test 内重估 train 尺子
- 新增未冻结 variant
- 看 backtest 后回写 selected_variants_test
- 只保留通过者，不保留全量 ledger
- 搜索量较大却不做 multiple testing 校正

## Checklist

Stage checklist:
- [blocking] standalone_alpha 场景下，Rank IC、ICIR、分组收益、单调性、breadth 和子窗口稳定性均已检查
- [blocking] regime_filter / combo_filter 场景下，target strategy reference 和 gated vs ungated 对比已冻结
- [blocking] test 使用的 preprocess、neutralization、bucket 和 rebalance 规则全部来自 train freeze
- [blocking] selected variants 和 rejected variants 都已保留，并可追溯决策理由
- [blocking] 未在 test 重估 train 尺子，也未新增未冻结的 variant
- [blocking] 若使用 filter 语义，check 结果体现条件改善而不是独立赚钱
- [reservation] 若存在多重测试或多个候选 variant，已保留完整 ledger 而非只保留通过项

## Audit-Only Items

Audit-only items:
- 证据表述是否足以让 reviewer 读懂角色差异
- 样本覆盖是否解释充分

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

- Default rollback stage: csf_test_evidence
- Allowed modification: 澄清文档表述
- Allowed modification: 补全缺失 artifact
- Allowed modification: 修正证据表述
- Must open child lineage when: factor_role 变化导致证据语义改变
- Must open child lineage when: 证据本体从截面排序改为别的任务

## Downstream Permissions

- May advance to: csf_backtest_ready
- Frozen output consumable by next stage: csf_selected_variants_test.csv
- Frozen output consumable by next stage: csf_test_contract.md
- Next stage must not consume/re-estimate: 未冻结的 test 搜索轨迹

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
