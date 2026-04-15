---
name: qros-csf-signal-ready-review
description: Codex review skill for CSF Signal Ready stage verification.
---

# CSF Signal Ready 审查

## 用途

将已冻结的截面研究语义实例化为可比较、可复现的因子面板合同

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- 已冻结的 csf_data_ready 输出
- 因子表达式或多因子组合草案
- 因子方向与时间语义提案

## 必需输出

必需输出:
- factor_panel.parquet
- factor_manifest.yaml
- factor_field_dictionary.md
- factor_coverage_report.parquet
- factor_contract.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：CSF Signal Ready

正式门禁摘要：
必须全部满足：
- factor_id / factor_version / factor_direction 已冻结
- factor_panel 可唯一表示同一时点不同资产的因子值
- 所有输入字段都来自 csf_data_ready
- 多因子组合公式是确定性的
- 缺失值、coverage、eligibility 传递规则已写清
- 因子方向明确，不允许到 test/backtest 再解释
以下任一情况都不得出现：
- 因子定义依赖 train/test/backtest 结果回写
- factor_panel 无法稳定重建
- 多因子组合权重在后续阶段才学习
- factor_direction 不清楚
- eligibility 与 factor computation 混成一团
- test 才知道的 quantile / cutoff 被偷写回 signal

## 审查清单

阶段检查项：
- [blocking] factor_role、factor_structure、portfolio_expression、neutralization_policy 均来自 mandate 冻结；non-standalone 具备 target_strategy_reference，group_neutral 具备 group_taxonomy_reference
- [blocking] factor_id、factor_version、factor_direction 已冻结
- [blocking] factor_panel 以统一面板主键唯一表示同一时点不同资产的因子值
- [blocking] raw_factor_fields、derived_factor_fields 和 final_score_field 已写清
- [blocking] 多因子组合公式是确定性的，不依赖 train-learned weights
- [blocking] 缺失值策略、coverage contract 和 eligibility 传递规则已冻结
- [blocking] 若需要组内排序或组中性化，factor group context 已冻结
- [blocking] 不得把过滤器语义伪装成独立 alpha 语义

## 仅审计项

仅审计项:
- 因子命名是否足够可读
- 多因子组合描述是否清楚

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

- 默认 rollback stage：csf_signal_ready
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正因子方向与组合公式
- 以下情况必须开 child lineage：因子结构从截面改为时序
- 以下情况必须开 child lineage：因子角色发生实质变化

## 下游权限

- 可进入下游阶段：csf_train_freeze
- 下游可直接消费的冻结产物：factor_panel.parquet
- 下游可直接消费的冻结产物：factor_manifest.yaml
- 下游可直接消费的冻结产物：factor_coverage_report.parquet
- 下游不得消费 / 重估：未冻结的 train 尺子

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
