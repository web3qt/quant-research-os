---
name: qros-backtest-ready-review
description: Codex review skill for Backtest Ready stage verification.
---

# Backtest Ready 审查

## 用途

用冻结后的候选集和交易规则验证策略可交易性与正式资金曲线口径

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- test_evidence frozen_spec.json
- selected_symbols_test.csv or selected_symbols_test.parquet
- frozen signal fields and best_h
- execution, portfolio and risk overlay rules

## 必需输出

必需输出:
- engine_compare.csv
- vectorbt/
- backtrader/
- strategy_combo_ledger.csv
- capacity_review.md
- backtest_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Backtest Ready

正式门禁摘要：
必须全部满足：
- 仅使用上游冻结的 whitelist、best_h 和交易规则身份
- vectorbt 与 backtrader 双引擎正式回测已完成
- 收益、Sharpe、回撤使用正式资金记账口径
- capacity_review 已写清 deployable capital、主要容量瓶颈、自冲击边界和成本吞噬位置
- 若触发 abnormal performance sanity check，则复核已完成且无阻断性问题
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
以下任一情况都不得出现：
- 只跑单一回测引擎就宣布 Backtest Ready
- 在 Backtest 内重新选币或重估 best_h
- 成本、容量或资金记账口径无法解释
- 双引擎存在语义冲突

## 审查清单

阶段检查项：
- [blocking] 输入白名单和交易规则来自上游冻结文件
- [blocking] vectorbt 与 backtrader 两套正式回测均已完成
- [blocking] 双引擎关键结果一致，semantic_gap = false
- [blocking] 收益、回撤和资金曲线基于正式资金记账口径
- [blocking] 未在 backtest 中重新选币或重估 best_h
- [blocking] 若收益异常高，abnormal performance sanity check 已完成
- [reservation] 若搜索多套策略组合，combo ledger 与预算纪律完整
- [reservation] gross / net / fee / turnover / close reason 已拆解解释

## 仅审计项

仅审计项:
- 容量假设的进一步补强
- 更重压力测试
- 主备方案收敛前的非阻断性 reservations

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
- `CHILD LINEAGE`: 需要以新谱系承接，不允许在原线静默改题

## Rollback 规则

- 默认 rollback stage：backtest_ready
- 允许修改：execution policy
- 允许修改：portfolio policy
- 允许修改：risk overlay
- 允许修改：cost model implementation
- 以下情况必须开 child lineage：想重写 alpha 机制
- 以下情况必须开 child lineage：想回头改 train thresholds 或 test whitelist

## 下游权限

- 可进入下游阶段：holdout_validation
- 下游可直接消费的冻结产物：selected strategy combo
- 下游可直接消费的冻结产物：backtest frozen config
- 下游可直接消费的冻结产物：engine_compare.csv
- 下游不得消费 / 重估：whitelist
- 下游不得消费 / 重估：best_h
- 下游不得消费 / 重估：core signal thresholds

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
10. 只有结果达到 closure-ready，才运行 `./.qros/bin/qros-review`
11. 复核最终生成的 closure artifacts
