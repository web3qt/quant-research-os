---
name: qros-holdout-validation-review
description: Codex review skill for Holdout Validation stage verification.
---

# Holdout Validation 审查

## 用途

用最终未参与设计的窗口验证冻结方案是否没有翻向

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- backtest frozen config
- selected strategy combo
- holdout window definition from mandate time split

## 必需输出

必需输出:
- holdout_run_manifest.json
- holdout_backtest_compare.csv
- holdout_gate_decision.md
- holdout window result files
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Holdout Validation

正式门禁摘要：
必须全部满足：
- 仅复用 Backtest 冻结方案，不改参数、不改白名单、不改交易规则
- 已生成单窗口和合并窗口结果
- 结果方向未发生无法解释的翻转
- 若 verdict 依赖“结构仍连续”或“结果退化只是 regime 不匹配而非机制断裂”的判断，已记录结构突变检验 protocol 或免做理由
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
以下任一情况都不得出现：
- 用 holdout 调参
- 用 holdout 改白名单
- 把“只是 regime 变了”或“关系仍连续”作为 holdout 通过依据，却没有说明结构突变检验 protocol 或免做理由
- 把 holdout 并回 test 或 backtest 当更多样本

## 审查清单

阶段检查项：
- [blocking] Holdout 使用的规则未再修改，且完全来自 Backtest 冻结方案
- [blocking] 单窗口和合并窗口结果均已落地
- [blocking] 未用 holdout 调任何参数、白名单或规则
- [blocking] 已解释无交易、低样本或低触发是否属于正常现象
- [blocking] 若 verdict 依赖结构连续性或用 regime mismatch 解释退化，已记录结构突变检验 protocol 或免做理由
- [reservation] 已检查 holdout 是否暴露孤峰参数、selection bias、断崖退化或显著结构突变
- [reservation] 若检出显著结构突变，已说明其更接近 regime mismatch、样本问题还是机制断裂

## 仅审计项

仅审计项:
- 低触发、低样本或无交易是否属于正常现象
- 细颗粒度漂移解释
- 结构突变与参数稳定性审计（例如 Chow、Bai-Perron、CUSUM、rolling coefficient stability）

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
- `GO_TO_MANDATE`: 想法通过 qualification，允许进入 mandate_confirmation_pending 并申请生成 Mandate 产物
- `NEEDS_REFRAME`: 方向可研究，但当前边界或变量定义不足，需按 required_reframe_actions 重写后再审
- `DROP`: 不值得投入进一步研究预算，终止该想法

## Rollback 规则

- 默认 rollback stage：holdout_validation
- 允许修改：holdout execution rerun
- 允许修改：holdout reporting
- 以下情况必须开 child lineage：想基于 holdout 结果改正式规则

## 下游权限

- 下游可直接消费的冻结产物：holdout_gate_decision.md
- 下游可直接消费的冻结产物：holdout_backtest_compare.csv
- 下游不得消费 / 重估：any research parameter
- 下游不得消费 / 重估：whitelist
- 下游不得消费 / 重估：best_h

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
