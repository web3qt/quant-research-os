---
name: qros-test-evidence-review
description: Codex review skill for Test Evidence stage verification.
---

# Test Evidence Review

## Purpose

用独立测试窗验证冻结后的统计结构，并冻结白名单与 best_h

## Shared Inputs

- `docs/gates/workflow_stage_gates.yaml`
- `docs/review-sop/review_checklist_master.yaml`
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
- 若 formal gate 直接引用 t 值、p 值、回归显著性或残差型证据，已记录稳健推断口径或免做理由
- 若 formal gate 依赖残差近似独立、原始 OLS 误差设定，或用“未见明显 serial correlation”支撑结论，已记录自相关诊断 protocol 或免做理由
- 若 formal gate 依赖多变量回归里单个系数的符号、显著性或增量解释，已记录多重共线性诊断 protocol 或免做理由
- 若 formal gate 把跨窗口关系连续性、回归系数稳定性、lead-lag 结构或 threshold 机制延续作为通过依据，已记录结构突变检验 protocol 或免做理由
- 若 formal gate 依赖可能非平稳 level series 的回归、长期均衡关系或 spread mean-reversion 结构，已记录防虚假回归 protocol 或免做理由
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
Must fail none of:
- 在 test 窗里重估 train 阈值
- 看了 backtest 再回写 test 白名单但没有 retry 记账
- 把未经说明的原始 OLS 显著性直接作为 formal gate 通过依据
- 把残差近似独立、原始 OLS 误差设定或“未见明显 serial correlation”直接作为 formal gate 通过依据，却没有说明自相关诊断 protocol 或免做理由
- 把多变量回归里单个系数的符号、显著性或增量解释直接作为 formal gate 通过依据，却没有说明多重共线性诊断 protocol 或免做理由
- 把跨窗口关系连续性或系数稳定性直接作为 formal gate 通过依据，却没有说明结构突变检验 protocol 或免做理由
- 把可能非平稳的 level-series 回归、长期均衡关系或 spread mean-reversion 直接作为 formal gate 通过依据，却没有说明防虚假回归 protocol 或免做理由
- 没有 frozen_spec 就把对象交给 Backtest

## Checklist

Stage checklist:
- [blocking] Test 使用的阈值完全来自 Train 冻结对象
- [blocking] formal gate 与 audit-only 已分开记录
- [blocking] 统计证据在独立样本上计算，未在 test 重估训练尺子
- [blocking] 白名单、best_h 或后续候选集已冻结
- [blocking] 未看了 Backtest 再回写 Test 白名单
- [blocking] 若 formal gate 引用了 t 值、p 值、回归显著性或残差型证据，已写明稳健推断口径或免做理由
- [blocking] 若 formal gate 依赖残差近似独立、原始 OLS 误差设定，或用“未见明显 serial correlation”支撑结论，已记录自相关诊断 protocol 或免做理由
- [blocking] 若 formal gate 依赖多变量回归里单个系数的符号、显著性或增量解释，已记录多重共线性诊断 protocol 或免做理由
- [blocking] 若 formal gate 把跨窗口关系连续性、回归系数稳定性或 lead-lag 结构延续作为通过依据，已记录结构突变检验 protocol 或免做理由
- [blocking] 若 formal gate 依赖可能非平稳 level series 的回归、长期均衡关系或 spread mean-reversion 结构，已记录防虚假回归 protocol 或免做理由
- [reservation] 若有条件分层分析，其定位为 audit evidence 或已明确冻结为正式 gate
- [reservation] 若做了自相关诊断，已说明 Durbin-Watson、Breusch-Godfrey LM、Ljung-Box 或同类方法的适用边界与结论
- [reservation] 若做了多重共线性诊断，已说明 VIF、condition number 或同类方法的适用边界与结论
- [reservation] 若做了结构突变或参数稳定性审计，已区分 regime mismatch、样本问题与机制失效
- [reservation] 若做了单位根、协整或防虚假回归诊断，已说明 ADF、Phillips-Perron、KPSS、Engle-Granger、Johansen 或同类方法的适用边界与结论

## Audit-Only Items

Audit-only items:
- HAC t 值
- 异方差/自相关稳健性说明（例如 Newey-West、White、Breusch-Pagan）
- 自相关诊断（例如 Durbin-Watson、Breusch-Godfrey LM、Ljung-Box）
- 多重共线性诊断（例如 VIF、condition number、pairwise correlation matrix）
- 结构突变检验或参数稳定性审计（例如 Chow、Bai-Perron、CUSUM、rolling coefficient stability）
- 防虚假回归与非平稳处理说明（例如 ADF、Phillips-Perron、KPSS、Engle-Granger、Johansen、returns/differencing）
- monotonic score
- 条件分层分析
- crowding overlap 与 factor distinctiveness 审计
- 高低波与下跌切片

## Closure Artifacts

- `latest_review_pack.yaml`
- `stage_gate_review.yaml`
- `stage_completion_certificate.yaml`

## Mandatory Adversarial Review Inputs

- `adversarial_review_request.yaml`
- lineage-local stage program source under the runtime-declared `required_program_dir`
- stage provenance in `program_execution_manifest.json`

## Mandatory Adversarial Reviewer Contract

You are the adversarial reviewer lane, not the original author.

Before any closure artifacts can exist:

1. Inspect `adversarial_review_request.yaml`
2. Verify your reviewer identity differs from `author_identity`
3. Inspect the lineage-local stage program source in `required_program_dir` and its `required_program_entrypoint`
4. Inspect the required artifacts and provenance named in the request
5. Write `adversarial_review_result.yaml`

`adversarial_review_result.yaml` must include at least:

- `review_cycle_id`
- `reviewer_identity`
- `reviewer_role`
- `reviewer_session_id`
- `reviewer_mode: adversarial`
- `review_loop_outcome`
- `reviewed_program_dir`
- `reviewed_program_entrypoint`
- `reviewed_artifact_paths`
- `reviewed_provenance_paths`
- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`

Allowed `review_loop_outcome` values:

- `FIX_REQUIRED`
- `CLOSURE_READY_PASS`
- `CLOSURE_READY_CONDITIONAL_PASS`
- `CLOSURE_READY_PASS_FOR_RETRY`
- `CLOSURE_READY_RETRY`
- `CLOSURE_READY_NO_GO`
- `CLOSURE_READY_CHILD_LINEAGE`

`FIX_REQUIRED` means: return the stage to the author for fixes; do not allow closure artifacts.

## Optional Reviewer Findings File

You may also create `review_findings.yaml` in the current `stage_dir` for human-readable detail and rollback metadata.

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
6. Inspect the lineage-local source code for this stage
7. Record audit-only findings after that
8. Save `adversarial_review_result.yaml` and, if useful, `review_findings.yaml`
9. If outcome is `FIX_REQUIRED`, return to the author lane and stop before closure
10. Only if the outcome is closure-ready, run `~/.qros/bin/qros-review`
11. Review the generated closure artifacts
