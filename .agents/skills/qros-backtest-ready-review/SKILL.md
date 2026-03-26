---
name: qros-backtest-ready-review
description: Codex review skill for Backtest Ready stage verification.
---

# Backtest Ready Review

## Purpose

用冻结后的候选集和交易规则验证策略可交易性与正式资金曲线口径

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- test_evidence frozen_spec.json
- selected_symbols_test.csv or selected_symbols_test.parquet
- frozen signal fields and best_h
- execution, portfolio and risk overlay rules

## Required Outputs

Required outputs:
- engine_compare.csv
- vectorbt/
- backtrader/
- strategy_combo_ledger.csv
- capacity_review.md
- backtest_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## Formal Gate

Stage: Backtest Ready

Formal gate summary:
Must pass all of:
- 仅使用上游冻结的 whitelist、best_h 和交易规则身份
- vectorbt 与 backtrader 双引擎正式回测已完成
- 收益、Sharpe、回撤使用正式资金记账口径
- capacity_review 已写清 deployable capital、主要容量瓶颈、自冲击边界和成本吞噬位置
- 若触发 abnormal performance sanity check，则复核已完成且无阻断性问题
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 只跑单一回测引擎就宣布 Backtest Ready
- 在 Backtest 内重新选币或重估 best_h
- 成本、容量或资金记账口径无法解释
- 双引擎存在语义冲突

## Checklist

Stage checklist:
- [blocking] 输入白名单和交易规则来自上游冻结文件
- [blocking] vectorbt 与 backtrader 两套正式回测均已完成
- [blocking] 双引擎关键结果一致，semantic_gap = false
- [blocking] 收益、回撤和资金曲线基于正式资金记账口径
- [blocking] 未在 backtest 中重新选币或重估 best_h
- [blocking] 若收益异常高，abnormal performance sanity check 已完成
- [reservation] 若搜索多套策略组合，combo ledger 与预算纪律完整
- [reservation] gross / net / fee / turnover / close reason 已拆解解释

## Audit-Only Items

Audit-only items:
- 容量假设的进一步补强
- 更重压力测试
- 主备方案收敛前的非阻断性 reservations

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

- Default rollback stage: backtest_ready
- Allowed modification: execution policy
- Allowed modification: portfolio policy
- Allowed modification: risk overlay
- Allowed modification: cost model implementation
- Must open child lineage when: 想重写 alpha 机制
- Must open child lineage when: 想回头改 train thresholds 或 test whitelist

## Downstream Permissions

- May advance to: holdout_validation
- Frozen output consumable by next stage: selected strategy combo
- Frozen output consumable by next stage: backtest frozen config
- Frozen output consumable by next stage: engine_compare.csv
- Next stage must not consume/re-estimate: whitelist
- Next stage must not consume/re-estimate: best_h
- Next stage must not consume/re-estimate: core signal thresholds

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
