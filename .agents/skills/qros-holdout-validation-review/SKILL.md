---
name: qros-holdout-validation-review
description: Codex review skill for Holdout Validation stage verification.
---

# Holdout Validation Review

## Purpose

用最终未参与设计的窗口验证冻结方案是否没有翻向

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- backtest frozen config
- selected strategy combo
- holdout window definition from mandate time split

## Required Outputs

Required outputs:
- holdout_run_manifest.json
- holdout_backtest_compare.csv
- holdout_gate_decision.md
- holdout window result files
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: Holdout Validation

Formal gate summary:
Must pass all of:
- 仅复用 Backtest 冻结方案，不改参数、不改白名单、不改交易规则
- 已生成单窗口和合并窗口结果
- 结果方向未发生无法解释的翻转
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 用 holdout 调参
- 用 holdout 改白名单
- 把 holdout 并回 test 或 backtest 当更多样本

## Checklist

Stage checklist:
- [blocking] Holdout 使用的规则未再修改，且完全来自 Backtest 冻结方案
- [blocking] 单窗口和合并窗口结果均已落地
- [blocking] 未用 holdout 调任何参数、白名单或规则
- [blocking] 已解释无交易、低样本或低触发是否属于正常现象
- [reservation] 已检查 holdout 是否暴露孤峰参数、selection bias 或断崖退化

## Audit-Only Items

Audit-only items:
- 低触发、低样本或无交易是否属于正常现象
- 细颗粒度漂移解释

## Closure Artifacts

- `latest_review_pack.yaml`
- `stage_gate_review.yaml`
- `stage_completion_certificate.yaml`

## Reviewer Findings File

Before writing closure artifacts, create `review_findings.yaml` in the current `stage_dir`.

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

## Rollback Rules

- Default rollback stage: holdout_validation
- Allowed modification: holdout execution rerun
- Allowed modification: holdout reporting
- Must open child lineage when: 想基于 holdout 结果改正式规则

## Downstream Permissions

- May advance to: promotion_decision
- Frozen output consumable by next stage: holdout_gate_decision.md
- Frozen output consumable by next stage: holdout_backtest_compare.csv
- Next stage must not consume/re-estimate: any research parameter
- Next stage must not consume/re-estimate: whitelist
- Next stage must not consume/re-estimate: best_h

## Verdict Flow

1. Confirm current stage
2. Load the stage contract
3. Load the stage checklist
4. Check required inputs and outputs
5. Evaluate the formal gate first
6. Record audit-only findings after that
7. Save `review_findings.yaml`
8. Run `~/.codex/qros/bin/qros-review`
9. Review the generated closure artifacts
