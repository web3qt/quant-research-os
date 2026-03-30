---
name: qros-csf-data-ready-review
description: Use when csf_data_ready artifacts have been authored and must pass formal gate review before advancing to csf_signal_ready stage.
---

# CSF Data Ready Review

## Purpose

验证 `csf_data_ready` 是否真的建立了可审计的 cross-sectional factor 面板底座与共享准入语义。

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- mandate frozen outputs
- `research_route.yaml`
- 原始市场数据或共享上游数据源
- 正式 universe 与时间边界

## Required Outputs

Required outputs:
- `panel_manifest.json`
- `asset_universe_membership.parquet`
- `eligibility_base_mask.parquet`
- `coverage_report.parquet`
- `shared_feature_base/`
- `csf_data_contract.md`
- `data_ready_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Formal Gate

Stage: CSF Data Ready

Formal gate summary:
Must pass all of:
- 面板主键、覆盖规则和准入语义已显式冻结
- date x asset 面板已生成，正式对象的面板时间轴一致
- 缺失、坏值、stale 和 outlier 语义已显式保留
- coverage_report 与 panel_manifest 已生成
- 排除项和准入结果已显式记录
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 没有统一面板栅格
- 把面板当成隐式时序表
- 静默吞掉缺失或静默 forward-fill
- universe 审计无法解释

## Checklist

Stage checklist:
- [blocking] date x asset 面板已生成，目标对象面板栅格一致
- [blocking] 缺失、stale、outlier、坏值等语义被显式标记，而非静默修复
- [blocking] 基础 universe 审计通过
- [blocking] panel_manifest 已冻结当前数据版本、Universe 版本和产物路径
- [blocking] 面板主键与覆盖口径明确，未混用时序语义
- [blocking] Universe 排除项已显式记录，并给出原因
- [reservation] shared_feature_base 或等价可复用共享层已生成

## Audit-Only Items

Audit-only items:
- 个别对象质量偏弱但未触发正式排除
- 共享派生层是否足够经济

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

- Default rollback stage: csf_data_ready
- Allowed modification: 面板抽取
- Allowed modification: 时间对齐
- Allowed modification: QC 规则
- Allowed modification: 准入审计
- Must open child lineage when: 想修改 mandate 冻结的时间边界
- Must open child lineage when: 想修改 mandate 冻结的 universe 口径

## Downstream Permissions

- May advance to: csf_signal_ready
- Frozen output consumable by next stage: `panel_manifest.json`
- Frozen output consumable by next stage: `asset_universe_membership.parquet`
- Frozen output consumable by next stage: `eligibility_base_mask.parquet`
- Frozen output consumable by next stage: `shared_feature_base/`
- Next stage must not consume/re-estimate: 正式时间边界
- Next stage must not consume/re-estimate: universe admission rules

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
