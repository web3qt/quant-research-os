---
name: qros-csf-train-freeze-review
description: Use when csf_train_freeze artifacts have been authored and must pass formal gate review before advancing to csf_test_evidence stage.
---

# CSF Train Freeze Review

## Purpose

验证 `csf_train_freeze` 是否真的把 cross-sectional factor 的预处理、中性化和分组尺子冻结好了。

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- csf_signal_ready frozen outputs
- `factor_manifest.yaml`
- `factor_panel.parquet`
- 训练窗基线数据

## Required Outputs

Required outputs:
- `csf_train_freeze.yaml`
- `train_quality.parquet`
- `train_variant_ledger.csv`
- `train_rejects.csv`
- `train_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Formal Gate

Stage: CSF Train Freeze

Formal gate summary:
Must pass all of:
- 预处理、中性化、分组和再平衡尺子已显式冻结
- 训练窗 quality 证据已生成
- 变体台账与拒绝台账已生成
- downstream 只能复用冻结尺子，不能重估
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 用下游结果回写 train 尺子
- 把 train 当成赢家选择器
- 台账不完整或拒绝原因缺失
- 预处理与中性化语义混用

## Checklist

Stage checklist:
- [blocking] preprocess、neutralization、bucket、rebalance 尺子已冻结
- [blocking] train_quality 已生成
- [blocking] train_variant_ledger 与 train_rejects 已生成
- [blocking] downstream 不得重估这些尺子
- [reservation] 若有可接受的 admissible set，已显式记录

## Audit-Only Items

Audit-only items:
- 少量弱覆盖变体
- 分组颗粒度是否可进一步收敛

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

- Default rollback stage: csf_train_freeze
- Allowed modification: 预处理规则
- Allowed modification: 中性化规则
- Allowed modification: 分组规则
- Allowed modification: 再平衡规则
- Must open child lineage when: 想回写 signal 定义或研究路线

## Downstream Permissions

- May advance to: csf_test_evidence
- Frozen output consumable by next stage: `csf_train_freeze.yaml`
- Frozen output consumable by next stage: `train_variant_ledger.csv`
- Frozen output consumable by next stage: `train_rejects.csv`
- Next stage must not consume/re-estimate: train 尺子
- Next stage must not consume/re-estimate: 预处理规则

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
