---
name: qros-data-ready-review
description: Codex review skill for Data Ready stage verification.
---

# Data Ready Review

## Purpose

产出共享、可审计、strategy-agnostic 的 Layer 0 数据基础层

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- mandate frozen outputs
- 原始市场数据或共享上游数据源
- 正式 universe 与时间边界

## Required Outputs

Required outputs:
- aligned_bars/
- rolling_stats/
- qc_report.parquet
- dataset_manifest.json
- validation_report.md
- data_contract.md
- dedupe_rule.md
- universe_summary.md
- universe_exclusions.csv
- universe_exclusions.md
- data_ready_gate_decision.md
- run_manifest.json
- rebuild_data_ready.py
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: Data Ready

Formal gate summary:
Must pass all of:
- 基准腿覆盖审计已完成
- dense 时间轴已生成，正式对象时间轴长度一致
- 缺失、坏价、stale 和 outlier 语义已显式保留
- qc_report 与 dataset_manifest 已生成
- 排除项和准入结果已显式记录
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
- run_manifest 已记录 runtime 版本、program_artifacts 和 replay_command
Must fail none of:
- 没有统一时间栅格
- 混用 open_time 和 close_time 作为主键
- 静默吞掉缺失或静默 forward-fill
- 基准腿覆盖或 universe 审计无法解释
- 只保存产物，没有 stage-local rebuild 程序或 replay 账本

## Checklist

Stage checklist:
- [blocking] dense 时间轴已生成，目标对象时间栅格一致
- [blocking] 缺失、stale、outlier、坏价等语义被显式标记，而非静默修复
- [blocking] 基准腿（如 BTC）覆盖审计通过
- [blocking] dataset_manifest.json 已冻结当前数据版本、Universe 版本和产物路径
- [blocking] 去重规则与时间主键口径明确，未混用 open_time / close_time
- [blocking] Universe 排除项已显式记录，并给出原因
- [blocking] run_manifest 已记录 replay_command，且 stage-local rebuild 程序已冻结
- [reservation] rolling_stats 或等价可复用 rolling 缓存已生成

## Audit-Only Items

Audit-only items:
- 个别对象质量偏弱但未触发正式排除
- rolling cache 选择是否足够经济

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
- `GO_TO_MANDATE`: 想法通过 qualification，允许进入 mandate_confirmation_pending 并申请生成 Mandate 产物
- `NEEDS_REFRAME`: 方向可研究，但当前边界或变量定义不足，需按 required_reframe_actions 重写后再审
- `DROP`: 不值得投入进一步研究预算，终止该想法

## Rollback Rules

- Default rollback stage: data_ready
- Allowed modification: 数据抽取
- Allowed modification: 时间对齐
- Allowed modification: QC 规则
- Allowed modification: admissibility 审计
- Must open child lineage when: 想修改 mandate 冻结的时间边界
- Must open child lineage when: 想修改 mandate 冻结的 universe 口径

## Downstream Permissions

- May advance to: signal_ready
- Frozen output consumable by next stage: aligned_bars/
- Frozen output consumable by next stage: rolling_stats/
- Frozen output consumable by next stage: qc_report.parquet
- Frozen output consumable by next stage: dataset_manifest.json
- Frozen output consumable by next stage: universe_fixed.csv
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
