---
name: qros-test-evidence-review
description: Use when test_evidence artifacts have been authored and must pass formal gate review before advancing to backtest_ready stage.
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
- [blocking] 上游 `04_train_freeze/stage_completion_certificate.yaml` 存在且 verdict 非 NO-GO / CHILD LINEAGE
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
- [reservation] 若仅给出原始 OLS 显著性而无异方差/自相关稳健性说明，不得升级为 formal pass 证据

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

## Reviewer Guidance

- 当 formal gate 直接引用时间序列回归、残差回归、因子收益回归或任何 `t`/`p` 显著性时，优先检查是否说明 `HAC / Newey-West` 等稳健口径。
- 当 formal gate 进一步依赖残差独立性或原始 `OLS` 误差设定时，检查是否说明 `Breusch-Godfrey LM`、`Durbin-Watson`、`Ljung-Box` 或同类 serial-correlation diagnostic，或写清免做理由。
- 当 formal gate 进一步依赖多变量回归里单个系数的符号、显著性或“控制后仍显著”的增量解释时，检查是否说明 `VIF`、`condition number` 或同类 multicollinearity diagnostic，或写清免做理由。
- 当 formal gate 声称 lead-lag、beta、threshold 机制或回归系数在 Train/Test 间稳定延续时，检查是否说明 `Chow`、`Bai-Perron`、`CUSUM` 或 rolling coefficient stability 等结构突变 protocol，或写清免做理由。
- 当 formal gate 依赖价格水平、OI、TVL、累计资金费率等可能非平稳 level series 的回归、长期均衡关系或 spread mean-reversion 结构时，检查是否说明 `ADF`、`Phillips-Perron`、`KPSS`、`Engle-Granger`、`Johansen` 或同类防虚假回归 protocol，或写清免做理由。
- 当主要风险在于方差不稳定而不是搜索噪声时，检查是否记录 `White` / `Breusch-Pagan` 诊断，或把 `WLS` / `GLS` / `ARCH` / `GARCH` 写入修正建议或 residual risks。
- `Breusch-Godfrey LM` 通常比 `Durbin-Watson` 更适合作为正式回归审计依据；`Durbin-Watson` 可以作为快速一阶检查，`Ljung-Box` 更适合作为补充审计。
- 高 `VIF` 不自动等于模型失效，但会削弱单个系数解释；pairwise correlation matrix 只能快速筛查，不能自动替代 `VIF` 或整体矩阵诊断。
- 不要把显著 break 机械等同于 `NO-GO`；先区分它更像 regime mismatch、样本过短，还是机制本身断裂。
- 不要把 regime stationarity audit、结构突变检验和单位根/协整问题混为一谈；它们分别对应窗口分布偏移、参数稳定性和 level-series 非平稳风险。
- 如果 series 非平稳且没有 cointegration 证据，level-series 的 `t` 值或高 `R^2` 不能直接支撑 formal `PASS`。
- 不要把具体统计库名当作要求；skill 只要求方法口径清楚、结论边界清楚。

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
8. Run `~/.qros/bin/qros-review`
9. Review the generated closure artifacts
