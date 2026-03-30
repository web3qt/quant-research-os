---
name: qros-csf-test-evidence-review
description: Use when csf_test_evidence artifacts have been authored and must pass formal gate review before advancing to csf_backtest_ready stage.
---

# CSF Test Evidence Review

## Purpose

验证 `csf_test_evidence` 是否真的把 cross-sectional factor 的证据层与候选冻结清楚。

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- csf_train_freeze frozen outputs
- `selected_factor_spec.json`
- 面板底座与训练窗冻结尺子

## Required Outputs

Required outputs:
- `rank_ic_timeseries.parquet`
- `bucket_returns.parquet`
- `admissibility_report.parquet`
- `factor_selection.csv`
- `factor_selection.parquet`
- `selected_factor_spec.json`
- `test_gate_table.csv`
- `test_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Formal Gate

Stage: CSF Test Evidence

Formal gate summary:
Must pass all of:
- standalone_alpha 与 filter/combo 的证据语义已分开
- 独立样本统计证据已生成
- selected_factor_spec 已冻结，且下游可直接消费
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 用 test 结果回写 train 尺子
- 只保留赢家而不保留可追溯的选择过程
- 把 filter/combo 当成 standalone alpha 去审
- 证据层不完整却宣布进入 backtest

## Checklist

Stage checklist:
- [blocking] standalone_alpha / filter-combo 证据已分流
- [blocking] rank IC、bucket returns 或 gated compare 已生成
- [blocking] admissibility 结果已生成
- [blocking] selected_factor_spec 已冻结
- [reservation] 若存在弱覆盖或 skipped variant，已显式记录

## Audit-Only Items

Audit-only items:
- 个别子窗口稳定性偏弱但不构成阻断
- factor 选择是否还能进一步收敛

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

- Default rollback stage: csf_test_evidence
- Allowed modification: 证据呈现
- Allowed modification: 候选冻结说明
- Allowed modification: admissibility 审计
- Must open child lineage when: 想修改 train 尺子或因子定义

## Downstream Permissions

- May advance to: csf_backtest_ready
- Frozen output consumable by next stage: `selected_factor_spec.json`
- Frozen output consumable by next stage: `factor_selection.csv`
- Frozen output consumable by next stage: `factor_selection.parquet`
- Next stage must not consume/re-estimate: train 尺子
- Next stage must not consume/re-estimate: 因子角色与组合表达

## Verdict Flow

1. Confirm current stage
2. Load the stage contract
3. Load the stage checklist
4. Check required inputs and outputs
5. Evaluate the formal gate first
6. Record audit-only findings after that
7. Save `review_findings.yaml`
8. Run `~/.qros/bin/qros-review`
9. Review the generated closure artifacts
