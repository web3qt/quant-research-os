---
name: qros-train-freeze-review
description: Use when train_freeze artifacts have been authored and must pass formal gate review before advancing to test_evidence stage.
---

# Train Calibration Review

## Purpose

在训练窗内冻结阈值、regime 切点、质量过滤和参数台账

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- signal_ready frozen outputs
- mandate time split and parameter grid
- 训练窗定义

## Required Outputs

Required outputs:
- train_thresholds.json
- train_quality.parquet
- train_param_ledger.csv
- train_rejects.csv
- train_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: Train Calibration

Formal gate summary:
Must pass all of:
- 所有训练阈值、regime 切点和辅助条件切点仅使用训练窗估计
- train_param_ledger 和 train_rejects 都已保存
- 保留与拒绝都有明确原因
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 用 test 或 backtest 结果回写 train 阈值
- 只保留通过参数，不保留完整搜索轨迹
- 没有冻结阈值就进入 Test

## Checklist

Stage checklist:
- [blocking] 训练阈值、分位尺子、regime 切点已冻结
- [blocking] 训练质量过滤已冻结，且未把 test/backtest 信息带入
- [blocking] 完整参数 ledger 已保存
- [blocking] reject ledger 已保存，并可解释拒绝原因
- [blocking] 没有用训练收益最大化直接选最终策略
- [blocking] 未根据 test/backtest 结果回写 train freeze
- [reservation] 若参数粗筛发生，理由仅限排除荒谬区间，而非后验收益优化

## Audit-Only Items

Audit-only items:
- 参数空间是否仍可继续 coarse-to-fine 收窄
- 某些辅助条件切点是否需要在 child lineage 单独升级

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

- Default rollback stage: train_calibration
- Allowed modification: train threshold estimation
- Allowed modification: quality filters
- Allowed modification: ledger generation
- Must open child lineage when: 借用 test 或 backtest 信息改 train 尺子
- Must open child lineage when: 引入新的正式机制变量

## Downstream Permissions

- May advance to: test_evidence
- Frozen output consumable by next stage: train_thresholds.json
- Frozen output consumable by next stage: train_param_ledger.csv
- Frozen output consumable by next stage: train_rejects.csv
- Next stage must not consume/re-estimate: frozen thresholds
- Next stage must not consume/re-estimate: frozen regime cuts
- Next stage must not consume/re-estimate: rejected param_id or symbol-param combinations

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
