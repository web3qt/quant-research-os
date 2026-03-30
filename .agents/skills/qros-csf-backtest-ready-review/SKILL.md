---
name: qros-csf-backtest-ready-review
description: Use when csf_backtest_ready artifacts have been authored and must pass formal gate review before advancing to csf_holdout_validation stage.
---

# CSF Backtest Ready Review

## Purpose

验证 `csf_backtest_ready` 是否真的把 cross-sectional factor 冻结成可交易组合合同与容量证据。

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/check-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## Required Inputs

Required inputs:
- csf_test_evidence frozen outputs
- `selected_factor_spec.json`
- `factor_role` / `portfolio_expression` 冻结语义

## Required Outputs

Required outputs:
- `frozen_portfolio_spec.json`
- `portfolio_weight_panel.parquet`
- `portfolio_curve.parquet`
- `engine_compare.csv`
- `vectorbt/`
- `backtrader/`
- `strategy_combo_ledger.csv`
- `capacity_review.md`
- `backtest_gate_decision.md`
- `artifact_catalog.md`
- `field_dictionary.md`

## Formal Gate

Stage: CSF Backtest Ready

Formal gate summary:
Must pass all of:
- 组合表达、风险覆盖和引擎合同已冻结
- 双引擎正式回测结果已完成
- 收益、回撤和资金曲线使用正式组合记账口径
- capacity_review 已写清 deployable capital、主要容量瓶颈和成本吞噬位置
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 在 backtest 内重新选择 factor 或重估 train 尺子
- 只跑一套回测结果就宣布完成
- 成本、容量或组合记账口径无法解释
- 组合表达与上游冻结语义冲突

## Checklist

Stage checklist:
- [blocking] 输入的 factor spec 与组合规则来自上游冻结文件
- [blocking] 双引擎正式回测已完成
- [blocking] portfolio_curve 与 portfolio_weight_panel 已生成
- [blocking] combo ledger 中 selection_rationale 非空
- [blocking] 未在 backtest 中重新选择 factor
- [reservation] 若存在 engine 差异，已记录解决规则或人工审核理由

## Audit-Only Items

Audit-only items:
- 容量假设的进一步补强
- 更重压力测试
- 主备组合方案收敛前的非阻断性保留

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

- Default rollback stage: csf_backtest_ready
- Allowed modification: 组合政策
- Allowed modification: 风险覆盖
- Allowed modification: 成本模型实现
- Allowed modification: 引擎合同
- Must open child lineage when: 想重写 factor 机制
- Must open child lineage when: 想回头改 train 尺子或 test 冻结对象

## Downstream Permissions

- May advance to: csf_holdout_validation
- Frozen output consumable by next stage: `frozen_portfolio_spec.json`
- Frozen output consumable by next stage: `strategy_combo_ledger.csv`
- Frozen output consumable by next stage: `portfolio_curve.parquet`
- Next stage must not consume/re-estimate: factor selection
- Next stage must not consume/re-estimate: train 尺子

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
