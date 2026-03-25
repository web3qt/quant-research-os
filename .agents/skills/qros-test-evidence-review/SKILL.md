---
name: qros-test-evidence-review
description: Codex review skill for Test Evidence stage verification.
---

# Test Evidence Review

## Purpose

用独立测试窗验证冻结后的统计结构，并冻结白名单与 best_h

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- signal_ready frozen timeseries
- train_thresholds.json
- train_param_ledger.csv
- data_ready aligned bars
- mandate time_split.json

## Required Outputs

Required outputs:
- report_by_h.parquet
- symbol_summary.parquet
- admissibility_report.parquet
- test_gate_table.csv
- crowding_review.md
- selected_symbols_test.csv
- selected_symbols_test.parquet
- frozen_spec.json
- test_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: Test Evidence

Formal gate summary:
Must pass all of:
- 仅使用 Train 已冻结的 thresholds、regime cuts 和保留对象
- formal gate 与 audit gate 已显式分开记录
- selected_symbols_test 与 best_h 已冻结
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 在 test 窗里重估 train 阈值
- 看了 backtest 再回写 test 白名单但没有 retry 记账
- 没有 frozen_spec 就把对象交给 Backtest

## Checklist

Stage checklist:
- [blocking] Test 使用的阈值完全来自 Train 冻结对象
- [blocking] formal gate 与 audit-only 已分开记录
- [blocking] 统计证据在独立样本上计算，未在 test 重估训练尺子
- [blocking] 白名单、best_h 或后续候选集已冻结
- [blocking] 未看了 Backtest 再回写 Test 白名单
- [reservation] 若有条件分层分析，其定位为 audit evidence 或已明确冻结为正式 gate

## Audit-Only Items

Audit-only items:
- HAC t 值
- monotonic score
- 条件分层分析
- crowding overlap 与 factor distinctiveness 审计
- 高低波与下跌切片

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

- Default rollback stage: test_evidence
- Allowed modification: 统计检验实现
- Allowed modification: frozen spec 生成
- Allowed modification: admissibility 聚合
- Must open child lineage when: 升级新的辅助条件层为正式机制
- Must open child lineage when: 想改变 formal gate 本身

## Downstream Permissions

- May advance to: backtest_ready
- Frozen output consumable by next stage: selected_symbols_test.csv
- Frozen output consumable by next stage: selected_symbols_test.parquet
- Frozen output consumable by next stage: frozen_spec.json
- Next stage must not consume/re-estimate: whitelist
- Next stage must not consume/re-estimate: best_h
- Next stage must not consume/re-estimate: formal gate thresholds

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
