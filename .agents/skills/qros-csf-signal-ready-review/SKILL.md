---
name: qros-csf-signal-ready-review
description: Use when csf_signal_ready artifacts have been authored and must pass formal gate review before advancing to csf_train_freeze stage.
---

# CSF Signal Ready Review

## Purpose

验证 `csf_signal_ready` 是否真的冻结了可复现的 cross-sectional factor 定义、角色和表达合同。

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- csf_data_ready frozen outputs
- `research_route.yaml`
- 面板底座与基础准入语义

## Required Outputs

Required outputs:
- `factor_panel.parquet`
- `factor_manifest.yaml`
- `factor_coverage.parquet`
- `factor_contract.md`
- `factor_field_dictionary.md`
- `signal_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Formal Gate

Stage: CSF Signal Ready

Formal gate summary:
Must pass all of:
- `factor_role`、`factor_structure`、`portfolio_expression` 与 `neutralization_policy` 已显式冻结
- factor panel 已生成，正式对象可复现且可比较
- 缺失、覆盖、方向与组合公式语义已显式保留
- factor_manifest 与 factor_coverage 已生成
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 因子定义回写到 data_ready
- 把面板当成时序单信号
- 多因子组合权重在本阶段依赖训练结果临时学习
- 因子方向或组合表达无法解释

## Checklist

Stage checklist:
- [blocking] factor_role 已冻结，且与研究路线一致
- [blocking] factor_structure 已冻结，且单因子/多因子语义明确
- [blocking] portfolio_expression 已冻结，且与后续组合表达一致
- [blocking] neutralization_policy 已冻结，group taxonomy 若启用已版本化
- [blocking] factor panel 可复现
- [reservation] 如有 skipped factor 或依赖关系，已显式记录

## Audit-Only Items

Audit-only items:
- 个别因子覆盖偏弱但未触发正式失败
- 组合公式是否足够经济

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

- Default rollback stage: csf_signal_ready
- Allowed modification: 因子身份
- Allowed modification: 因子结构
- Allowed modification: 组合表达
- Allowed modification: 中性化策略
- Must open child lineage when: 想改变研究路线或角色定义

## Downstream Permissions

- May advance to: csf_train_freeze
- Frozen output consumable by next stage: `factor_panel.parquet`
- Frozen output consumable by next stage: `factor_manifest.yaml`
- Frozen output consumable by next stage: `factor_coverage.parquet`
- Frozen output consumable by next stage: `factor_contract.md`
- Next stage must not consume/re-estimate: 面板准入语义
- Next stage must not consume/re-estimate: 因子身份

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
