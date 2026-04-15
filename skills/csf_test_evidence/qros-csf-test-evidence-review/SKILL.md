---
name: qros-csf-test-evidence-review
description: Codex review skill for CSF Test Evidence stage verification.
---

# CSF Test Evidence 审查

## 用途

在独立样本里验证截面因子排序能力或 filter / combo 条件改善能力

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- 已冻结的 csf_train_freeze 输出
- 独立测试窗
- factor_role / target_strategy_reference

## 必需输出

必需输出:
- csf_test_gate_table.csv
- csf_selected_variants_test.csv
- csf_test_contract.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：CSF Test Evidence

正式门禁摘要：
必须全部满足：
- 只复用 csf_train_freeze 的 frozen rules
- `standalone_alpha` 使用 Rank IC / ICIR / bucket spread / monotonicity / breadth / stability
- `regime_filter / combo_filter` 使用 gated vs ungated 改善证据
- 全量 test ledger 保留
- selected / rejected variants 有显式记账
以下任一情况都不得出现：
- test 内重估 train 尺子
- 新增未冻结 variant
- 看 backtest 后回写 selected_variants_test
- 只保留通过者，不保留全量 ledger
- 搜索量较大却不做 multiple testing 校正

## 审查清单

阶段检查项：
- [blocking] standalone_alpha 场景下，Rank IC、ICIR、分组收益、单调性、breadth 和子窗口稳定性均已检查
- [blocking] regime_filter / combo_filter 场景下，target strategy reference 和 gated vs ungated 对比已冻结
- [blocking] test 使用的 preprocess、neutralization、bucket 和 rebalance 规则全部来自 train freeze
- [blocking] selected variants 和 rejected variants 都已保留，并可追溯决策理由
- [blocking] 未在 test 重估 train 尺子，也未新增未冻结的 variant
- [blocking] 若使用 filter 语义，check 结果体现条件改善而不是独立赚钱
- [reservation] 若存在多重测试或多个候选 variant，已保留完整 ledger 而非只保留通过项

## 仅审计项

仅审计项:
- 证据表述是否足以让 reviewer 读懂角色差异
- 样本覆盖是否解释充分

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

- 默认 rollback stage：csf_test_evidence
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正证据表述
- 以下情况必须开 child lineage：factor_role 变化导致证据语义改变
- 以下情况必须开 child lineage：证据本体从截面排序改为别的任务

## 下游权限

- 可进入下游阶段：csf_backtest_ready
- 下游可直接消费的冻结产物：csf_selected_variants_test.csv
- 下游可直接消费的冻结产物：csf_test_contract.md
- 下游不得消费 / 重估：未冻结的 test 搜索轨迹

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
