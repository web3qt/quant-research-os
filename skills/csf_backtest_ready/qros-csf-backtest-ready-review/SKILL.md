---
name: qros-csf-backtest-ready-review
description: Codex review skill for CSF Backtest Ready stage verification.
---

# CSF Backtest Ready 审查

## 用途

将冻结后的因子分数映射成正式组合，并验证成本后的经济可行性

## 共用输入

- `docs/gates/workflow_stage_gates.yaml`
- `docs/review-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- 已冻结的 csf_test_evidence 输出
- portfolio_expression 提案
- cost / capacity 提案

## 必需输出

必需输出:
- portfolio_contract.yaml
- portfolio_weight_panel.parquet
- rebalance_ledger.csv
- turnover_capacity_report.parquet
- cost_assumption_report.md
- engine_compare.csv
- portfolio_summary.parquet
- name_level_metrics.parquet
- drawdown_report.json
- csf_backtest_gate_table.csv
- csf_backtest_contract.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：CSF Backtest Ready

正式门禁摘要：
必须全部满足：
- 只消费 csf_selected_variants_test 中通过的 variants
- 组合规则 machine-readable 冻结
- 成本后结果仍具经济意义
- 换手、容量、参与率分析完整
- 组合结果不是极少数 name 或日期单独支撑
- 组合表达与 mandate 冻结一致
以下任一情况都不得出现：
- backtest 内重新挑选 variant
- 改变 long/short cut 或权重规则却不回退
- 只报 gross，不报 net after cost
- 没有 name-level concentration 诊断
- 容量分析缺失
- 结果只靠单一极端窗口或单一资产支撑

## 审查清单

阶段检查项：
- [blocking] backtest 只消费 test 阶段冻结通过的 variant 与组合规则
- [blocking] portfolio_expression 已冻结且与 factor_role 匹配：standalone_alpha 只能使用独立组合表达，regime_filter 只允许 target_strategy_filter，combo_filter 只允许 target_strategy_filter / target_strategy_overlay
- [blocking] weight mapping、gross / net exposure、turnover、cost 和 capacity 口径已冻结
- [blocking] 净收益、回撤和资金曲线基于正式资金记账口径
- [blocking] 未在 backtest 中重新挑选 variant、重估权重或改写组合规则
- [blocking] 若为 regime_filter / combo_filter，target strategy compare 与 gated / ungated summary 已一并冻结
- [reservation] name-level concentration、engine compare 和异常收益 sanity check 已保留

## 仅审计项

仅审计项:
- 组合表达是否足够清晰
- 成本假设是否解释充分

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

- 默认 rollback stage：csf_backtest_ready
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正组合权重和成本假设
- 以下情况必须开 child lineage：portfolio_expression 大类变化
- 以下情况必须开 child lineage：组合表达从截面切到别的研究问题

## 下游权限

- 可进入下游阶段：csf_holdout_validation
- 下游可直接消费的冻结产物：portfolio_contract.yaml
- 下游可直接消费的冻结产物：portfolio_weight_panel.parquet
- 下游可直接消费的冻结产物：csf_backtest_gate_table.csv
- 下游不得消费 / 重估：未冻结的权重搜索轨迹

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
