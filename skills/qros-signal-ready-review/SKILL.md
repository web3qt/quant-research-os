---
name: qros-signal-ready-review
description: Codex review skill for Signal Ready stage verification.
---

# Signal Ready Review

## Purpose

把 mandate 已冻结的表达式模板实例化成统一 schema 的正式信号层

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- mandate frozen outputs
- data_ready frozen outputs
- 已冻结的 signal expression template

## Required Outputs

Required outputs:
- param_manifest.csv
- params/
- signal_coverage.csv
- signal_coverage.md
- signal_coverage_summary.md
- signal_contract.md
- signal_fields_contract.md
- signal_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: Signal Ready

Formal gate summary:
Must pass all of:
- 已显式物化 baseline 或 declared search_batch 的全部 param_id
- param_id 身份清晰且有 param_manifest
- 正式 timeseries schema、参数元数据和时间语义已冻结
- signal gate 文档已生成
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- baseline 或 required param_id 物化失败
- failed symbols 或 failed params 大于零
- 下游才发现 signal contract 缺失或字段越层
- 在 Train 阶段才首次引入未曾在 Signal Ready 物化过的 param_id

## Checklist

Stage checklist:
- [blocking] 信号字段合同已生成，字段 schema 固定
- [blocking] param_id 身份已显式落地，并存在 param manifest
- [blocking] timeseries 已落盘，且下游无需临时重算同名信号
- [blocking] 当前阶段引用了上游 Mandate 的表达式模板，而未静默改写机制
- [blocking] 未越权做白名单结论、收益结论或 test/backtest 级别结论
- [reservation] coverage / low_sample / pair_missing 等最小质量保留项已审计
- [blocking] Train 阶段只能消费已在本阶段显式物化过的 param_id

## Audit-Only Items

Audit-only items:
- finite coverage、low_sample_rate、pair_missing_rate 等质量摘要
- search batch 中非阻断性的稀疏参数组

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

- Default rollback stage: signal_ready
- Allowed modification: signal 实现
- Allowed modification: 字段命名
- Allowed modification: 标签对齐
- Allowed modification: companion docs
- Must open child lineage when: 改变信号机制模板
- Must open child lineage when: 改变字段分层边界

## Downstream Permissions

- May advance to: train_calibration
- Frozen output consumable by next stage: param_manifest.csv
- Frozen output consumable by next stage: params/
- Frozen output consumable by next stage: signal_coverage.csv
- Frozen output consumable by next stage: signal_fields_contract.md
- Next stage must not consume/re-estimate: signal definition
- Next stage must not consume/re-estimate: param identity space

## Verdict Flow

1. Confirm current stage
2. Load the stage contract
3. Load the stage checklist
4. Check required inputs and outputs
5. Evaluate the formal gate first
6. Record audit-only findings after that
7. Save `review_findings.yaml`
8. Run `python scripts/run_stage_review.py`
9. Review the generated closure artifacts
