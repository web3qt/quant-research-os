---
name: qros-train-freeze-review
description: Codex review skill for Train Calibration stage verification.
---

# Train Calibration 审查

## 用途

在训练窗内冻结阈值、regime 切点、质量过滤和参数台账

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- signal_ready frozen outputs
- mandate time split and parameter grid
- 训练窗定义

## 必需输出

必需输出:
- train_thresholds.json
- train_quality.parquet
- train_param_ledger.csv
- train_rejects.csv
- train_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Train Calibration

正式门禁摘要：
必须全部满足：
- 所有训练阈值、regime 切点和辅助条件切点仅使用训练窗估计
- train_param_ledger 和 train_rejects 都已保存
- 保留与拒绝都有明确原因
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
以下任一情况都不得出现：
- 用 test 或 backtest 结果回写 train 阈值
- 只保留通过参数，不保留完整搜索轨迹
- 没有冻结阈值就进入 Test

## 审查清单

阶段检查项：
- [blocking] 训练阈值、分位尺子、regime 切点已冻结
- [blocking] 训练质量过滤已冻结，且未把 test/backtest 信息带入
- [blocking] 完整参数 ledger 已保存
- [blocking] reject ledger 已保存，并可解释拒绝原因
- [blocking] 没有用训练收益最大化直接选最终策略
- [blocking] 未根据 test/backtest 结果回写 train freeze
- [reservation] 若参数粗筛发生，理由仅限排除荒谬区间，而非后验收益优化

## 仅审计项

仅审计项:
- 参数空间是否仍可继续 coarse-to-fine 收窄
- 某些辅助条件切点是否需要在 child lineage 单独升级

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

- 默认 rollback stage：train_calibration
- 允许修改：train threshold estimation
- 允许修改：quality filters
- 允许修改：ledger generation
- 以下情况必须开 child lineage：借用 test 或 backtest 信息改 train 尺子
- 以下情况必须开 child lineage：引入新的正式机制变量

## 下游权限

- 可进入下游阶段：test_evidence
- 下游可直接消费的冻结产物：train_thresholds.json
- 下游可直接消费的冻结产物：train_param_ledger.csv
- 下游可直接消费的冻结产物：train_rejects.csv
- 下游不得消费 / 重估：frozen thresholds
- 下游不得消费 / 重估：frozen regime cuts
- 下游不得消费 / 重估：rejected param_id or symbol-param combinations

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
