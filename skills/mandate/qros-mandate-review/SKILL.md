---
name: qros-mandate-review
description: Codex review skill for Mandate stage verification.
---

# Mandate 审查

## 用途

冻结研究主问题、时间边界、universe、字段层级和参数边界

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- 研究主题说明或专题草稿
- 候选 universe 与时间边界提案
- 字段族、公式模板、实现栈和并行计划提案

## 必需输出

必需输出:
- mandate.md
- research_scope.md
- time_split.json
- parameter_grid.yaml
- run_config.toml
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Mandate

正式门禁摘要：
必须全部满足：
- 研究主问题与明确禁止事项已冻结
- 正式时间窗、切分方式、time label 和 no-lookahead 约定已冻结
- 正式 universe、准入口径和字段分层已冻结
- 参数字典、公式模板、实现栈、parallelization_plan 和 non_rust_exceptions 已写清
- 后续 crowding distinctiveness review 的比较基准，以及 capacity review 的流动性代理、参与率边界和自冲击假设边界已写清
- required_outputs 全部存在，且 machine-readable artifact 都能追到 companion field documentation
以下任一情况都不得出现：
- required_outputs 缺失
- 时间窗、universe 或无前视边界未冻结
- 只有裸字段名或裸参数名，没有字段解释和参数字典
- 研究问题被后验结果倒逼修改但没有重置 mandate

## 审查清单

阶段检查项：
- [blocking] 研究主问题已冻结，且明确写清不研究什么
- [blocking] 正式时间窗与 Train/Test/Backtest/Holdout 切分已冻结
- [blocking] Universe、准入口径、主副腿角色已冻结
- [blocking] 字段分层已写清，且关键字段具有人类可读解释
- [blocking] 信号表达式模板、时间语义和无前视约定已写清
- [blocking] 参数字典、参数候选集、参数约束已写清
- [reservation] 实现栈、并行计划、非 Rust 例外说明已记录
- [blocking] 若关键字段或参数仅列名称未解释，则不得通过
- [blocking] 若 research_route = cross_sectional_factor，则 factor_role、factor_structure、portfolio_expression、neutralization_policy 已冻结；且 non-standalone 需要 target_strategy_reference，group_neutral 需要 group_taxonomy_reference

## 仅审计项

仅审计项:
- 专题样板写法是否足够清楚
- 字段命名是否优雅或便于新成员阅读

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

- 默认 rollback stage：mandate
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正字段解释、参数字典和目录契约
- 以下情况必须开 child lineage：主问题改变
- 以下情况必须开 child lineage：universe 改变
- 以下情况必须开 child lineage：time split 改变
- 以下情况必须开 child lineage：机制模板改变

## 下游权限

- 可进入下游阶段：data_ready
- 可进入下游阶段：csf_data_ready
- 下游可直接消费的冻结产物：time_split.json
- 下游可直接消费的冻结产物：parameter_grid.yaml
- 下游可直接消费的冻结产物：run_config.toml
- 下游不得消费 / 重估：test results
- 下游不得消费 / 重估：backtest results
- 下游不得消费 / 重估：holdout results

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
