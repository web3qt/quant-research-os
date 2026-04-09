---
name: qros-test-evidence-review
description: Codex review skill for Test Evidence stage verification.
---

# Test Evidence 审查

## 用途

用独立测试窗验证冻结后的统计结构，并冻结白名单与 best_h

## 共用输入

- `docs/gates/workflow_stage_gates.yaml`
- `docs/review-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- signal_ready frozen timeseries
- train_thresholds.json
- train_param_ledger.csv
- data_ready aligned bars
- mandate time_split.json

## 必需输出

必需输出:
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

## 正式门禁

阶段：Test Evidence

正式门禁摘要：
必须全部满足：
- 仅使用 Train 已冻结的 thresholds、regime cuts 和保留对象
- formal gate 与 audit gate 已显式分开记录
- selected_symbols_test 与 best_h 已冻结
- 若 formal gate 直接引用 t 值、p 值、回归显著性或残差型证据，已记录稳健推断口径或免做理由
- 若 formal gate 依赖残差近似独立、原始 OLS 误差设定，或用“未见明显 serial correlation”支撑结论，已记录自相关诊断 protocol 或免做理由
- 若 formal gate 依赖多变量回归里单个系数的符号、显著性或增量解释，已记录多重共线性诊断 protocol 或免做理由
- 若 formal gate 把跨窗口关系连续性、回归系数稳定性、lead-lag 结构或 threshold 机制延续作为通过依据，已记录结构突变检验 protocol 或免做理由
- 若 formal gate 依赖可能非平稳 level series 的回归、长期均衡关系或 spread mean-reversion 结构，已记录防虚假回归 protocol 或免做理由
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
以下任一情况都不得出现：
- 在 test 窗里重估 train 阈值
- 看了 backtest 再回写 test 白名单但没有 retry 记账
- 把未经说明的原始 OLS 显著性直接作为 formal gate 通过依据
- 把残差近似独立、原始 OLS 误差设定或“未见明显 serial correlation”直接作为 formal gate 通过依据，却没有说明自相关诊断 protocol 或免做理由
- 把多变量回归里单个系数的符号、显著性或增量解释直接作为 formal gate 通过依据，却没有说明多重共线性诊断 protocol 或免做理由
- 把跨窗口关系连续性或系数稳定性直接作为 formal gate 通过依据，却没有说明结构突变检验 protocol 或免做理由
- 把可能非平稳的 level-series 回归、长期均衡关系或 spread mean-reversion 直接作为 formal gate 通过依据，却没有说明防虚假回归 protocol 或免做理由
- 没有 frozen_spec 就把对象交给 Backtest

## 审查清单

阶段检查项：
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

## 仅审计项

仅审计项:
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

## Closure 产物

- `latest_review_pack.yaml`
- `stage_gate_review.yaml`
- `stage_completion_certificate.yaml`

## 强制对抗审查输入

- `adversarial_review_request.yaml`
- lineage-local stage program source under the runtime-declared `required_program_dir`
- stage provenance in `program_execution_manifest.json`

## 强制对抗审查 Reviewer 合同

你是 `adversarial reviewer-agent` 这条审查分支，不是原始 author。

在任何 closure artifacts 出现之前：

1. 检查 `adversarial_review_request.yaml`
2. 确认你的 reviewer identity 与 `author_identity` 不同
3. 对 `required_program_dir` 和 `required_program_entrypoint` 执行源码检查（`source-code inspection`）
4. 检查 request 中列出的必需 artifacts 与 provenance
5. 写出 `adversarial_review_result.yaml`

`adversarial_review_result.yaml` 至少必须包含：

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

允许的 `review_loop_outcome` 取值：

- `FIX_REQUIRED`
- `CLOSURE_READY_PASS`
- `CLOSURE_READY_CONDITIONAL_PASS`
- `CLOSURE_READY_PASS_FOR_RETRY`
- `CLOSURE_READY_RETRY`
- `CLOSURE_READY_NO_GO`
- `CLOSURE_READY_CHILD_LINEAGE`

`FIX_REQUIRED` 的含义是：退回 author 修复；不得允许 closure artifacts 出现。

`closure-ready adverse verdict` 路径包括 `CLOSURE_READY_NO_GO`、`CLOSURE_READY_CHILD_LINEAGE`，以及其它等价的 closure-ready terminal failure outcome；这些结果可以继续进入 deterministic closure writing 与 downstream failure routing。

## 可选 Reviewer Findings 文件

你也可以在当前 `stage_dir` 下额外创建 `review_findings.yaml`，用于保存面向人的说明和 rollback metadata。

最低建议字段：

- `blocking_findings`
- `reservation_findings`
- `info_findings`
- `residual_risks`
- `recommended_verdict`
- `rollback_stage`
- `allowed_modifications`

`review_findings.yaml` 负责承载语义判断；hard evidence checks 与最终 closure artifacts 仍交给 review engine 处理。

## 允许的 Verdict

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

## Rollback 规则

- 默认 rollback stage：test_evidence
- 允许修改：统计检验实现
- 允许修改：frozen spec 生成
- 允许修改：admissibility 聚合
- 以下情况必须开 child lineage：升级新的辅助条件层为正式机制
- 以下情况必须开 child lineage：想改变 formal gate 本身

## 下游权限

- 可进入下游阶段：backtest_ready
- 下游可直接消费的冻结产物：selected_symbols_test.csv
- 下游可直接消费的冻结产物：selected_symbols_test.parquet
- 下游可直接消费的冻结产物：frozen_spec.json
- 下游不得消费 / 重估：whitelist
- 下游不得消费 / 重估：best_h
- 下游不得消费 / 重估：formal gate thresholds

## Verdict 流程

1. 确认当前 stage
2. 读取 stage contract
3. 读取 stage checklist
4. 检查 required inputs 与 outputs
5. 先判断 formal gate
6. 检查该阶段的 lineage-local 源码与程序实现
7. 再记录 audit-only findings
8. 保存 `adversarial_review_result.yaml`；如有必要，再保存 `review_findings.yaml`
9. 如果结果是 `FIX_REQUIRED`，退回 author lane，并在 closure 前停止
10. 只有结果达到 closure-ready，才运行 `~/.qros/bin/qros-review`
11. 复核最终生成的 closure artifacts
