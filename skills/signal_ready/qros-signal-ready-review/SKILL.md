---
name: qros-signal-ready-review
description: Codex review skill for Signal Ready stage verification.
---

# Signal Ready 审查

## 用途

把 mandate 已冻结的表达式模板实例化成统一 schema 的正式信号层

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- mandate frozen outputs
- data_ready frozen outputs
- 已冻结的 signal expression template

## 必需输出

必需输出:
- param_manifest.csv
- params/
- signal_coverage.csv
- signal_coverage.md
- signal_coverage_summary.md
- signal_contract.md
- signal_fields_contract.md
- signal_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Signal Ready

正式门禁摘要：
必须全部满足：
- 已显式物化 baseline 或 declared search_batch 的全部 param_id
- param_id 身份清晰且有 param_manifest
- 正式 timeseries schema、参数元数据和时间语义已冻结
- signal gate 文档已生成
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
以下任一情况都不得出现：
- baseline 或 required param_id 物化失败
- failed symbols 或 failed params 大于零
- 下游才发现 signal contract 缺失或字段越层
- 在 Train 阶段才首次引入未曾在 Signal Ready 物化过的 param_id

## 审查清单

阶段检查项：
- [blocking] 信号字段合同已生成，字段 schema 固定
- [blocking] param_id 身份已显式落地，并存在 param manifest
- [blocking] timeseries 已落盘，且下游无需临时重算同名信号
- [blocking] 当前阶段引用了上游 Mandate 的表达式模板，而未静默改写机制
- [blocking] 未越权做白名单结论、收益结论或 test/backtest 级别结论
- [reservation] coverage / low_sample / pair_missing 等最小质量保留项已审计
- [blocking] Train 阶段只能消费已在本阶段显式物化过的 param_id

## 仅审计项

仅审计项:
- finite coverage、low_sample_rate、pair_missing_rate 等质量摘要
- search batch 中非阻断性的稀疏参数组

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

- 默认 rollback stage：signal_ready
- 允许修改：signal 实现
- 允许修改：字段命名
- 允许修改：标签对齐
- 允许修改：companion docs
- 以下情况必须开 child lineage：改变信号机制模板
- 以下情况必须开 child lineage：改变字段分层边界

## 下游权限

- 可进入下游阶段：train_calibration
- 下游可直接消费的冻结产物：param_manifest.csv
- 下游可直接消费的冻结产物：params/
- 下游可直接消费的冻结产物：signal_coverage.csv
- 下游可直接消费的冻结产物：signal_fields_contract.md
- 下游不得消费 / 重估：signal definition
- 下游不得消费 / 重估：param identity space

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
