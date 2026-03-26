---
name: qros-mandate-review
description: Codex review skill for Mandate stage verification.
---

# Mandate Review

## Purpose

冻结研究主问题、时间边界、universe、字段层级和参数边界

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- 研究主题说明或专题草稿
- 候选 universe 与时间边界提案
- 字段族、公式模板、实现栈和并行计划提案

## Required Outputs

Required outputs:
- mandate.md
- research_scope.md
- time_split.json
- parameter_grid.yaml
- run_config.toml
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: Mandate

Formal gate summary:
Must pass all of:
- 研究主问题与明确禁止事项已冻结
- 正式时间窗、切分方式、time label 和 no-lookahead 约定已冻结
- 正式 universe、准入口径和字段分层已冻结
- 参数字典、公式模板、实现栈、parallelization_plan 和 non_rust_exceptions 已写清
- 后续 crowding distinctiveness review 的比较基准，以及 capacity review 的流动性代理、参与率边界和自冲击假设边界已写清
- required_outputs 全部存在，且 machine-readable artifact 都能追到 companion field documentation
Must fail none of:
- required_outputs 缺失
- 时间窗、universe 或无前视边界未冻结
- 只有裸字段名或裸参数名，没有字段解释和参数字典
- 研究问题被后验结果倒逼修改但没有重置 mandate

## Checklist

Stage checklist:
- [blocking] 研究主问题已冻结，且明确写清不研究什么
- [blocking] 正式时间窗与 Train/Test/Backtest/Holdout 切分已冻结
- [blocking] Universe、准入口径、主副腿角色已冻结
- [blocking] 字段分层已写清，且关键字段具有人类可读解释
- [blocking] 信号表达式模板、时间语义和无前视约定已写清
- [blocking] 参数字典、参数候选集、参数约束已写清
- [reservation] 实现栈、并行计划、非 Rust 例外说明已记录
- [blocking] 若关键字段或参数仅列名称未解释，则不得通过

## Audit-Only Items

Audit-only items:
- 专题样板写法是否足够清楚
- 字段命名是否优雅或便于新成员阅读

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

- Default rollback stage: mandate
- Allowed modification: 澄清文档表述
- Allowed modification: 补全缺失 artifact
- Allowed modification: 修正字段解释、参数字典和目录契约
- Must open child lineage when: 主问题改变
- Must open child lineage when: universe 改变
- Must open child lineage when: time split 改变
- Must open child lineage when: 机制模板改变

## Downstream Permissions

- May advance to: data_ready
- Frozen output consumable by next stage: time_split.json
- Frozen output consumable by next stage: parameter_grid.yaml
- Frozen output consumable by next stage: run_config.toml
- Next stage must not consume/re-estimate: test results
- Next stage must not consume/re-estimate: backtest results
- Next stage must not consume/re-estimate: holdout results

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
