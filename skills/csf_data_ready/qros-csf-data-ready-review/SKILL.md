---
name: qros-csf-data-ready-review
description: Codex review skill for CSF Data Ready stage verification.
---

# CSF Data Ready 审查

## 用途

产出截面因子路线的 date x asset 面板底座、universe membership 和 eligibility mask

## 共用输入

- `docs/gates/workflow_stage_gates.yaml`
- `docs/review-sop/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- mandate frozen outputs
- 截面 universe 提案
- 截面共享字段底座提案

## 必需输出

必需输出:
- panel_manifest.json
- asset_universe_membership.parquet
- cross_section_coverage.parquet
- eligibility_base_mask.parquet
- shared_feature_base/
- csf_data_contract.md
- run_manifest.json
- rebuild_csf_data_ready.py
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：CSF Data Ready

正式门禁摘要：
必须全部满足：
- 面板主键明确且唯一：date + asset
- 截面覆盖可审计
- universe membership 显式记录
- eligibility mask 作为独立底座存在
- 共享字段具备时间语义和缺失语义
- 如允许 group_neutral，taxonomy 已冻结或显式版本化
- run_manifest 已记录 runtime 版本、program_artifacts 和 replay_command
以下任一情况都不得出现：
- 只有资产时序表，没有显式截面面板合同
- universe membership 无法按日期重建
- eligibility 规则混在下游因子代码里
- 覆盖率波动显著却没有报告
- 分组中性化需要的 taxonomy 在下游临时补
- 只保存产物，没有 stage-local rebuild 程序或 replay 账本

## 审查清单

阶段检查项：
- [blocking] 已形成显式的 date x asset 面板合同，而不是零散资产时序表
- [blocking] universe membership 按日期显式记录且可重建
- [blocking] eligibility_base_mask 作为独立底座冻结，未混入后续因子逻辑
- [blocking] 截面覆盖、缺失和共享字段语义已显式记录
- [blocking] 若后续允许 group_neutral，group taxonomy 已冻结或版本化
- [blocking] artifact catalog 与 field dictionary 已同步登记 CSF 数据底座
- [blocking] run_manifest 已记录 replay_command，且 stage-local rebuild 程序已冻结
- [reservation] 覆盖率波动、边缘样本或 taxonomy 版本切换均已明确记录在审查材料中

## 仅审计项

仅审计项:
- 面板字段命名是否清楚
- 共享字段说明是否便于 reviewer 追踪

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

- 默认 rollback stage：csf_data_ready
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正截面面板主键与 membership 规则
- 以下情况必须开 child lineage：面板主键改变
- 以下情况必须开 child lineage：universe 改变
- 以下情况必须开 child lineage：eligibility 语义改变

## 下游权限

- 可进入下游阶段：csf_signal_ready
- 下游可直接消费的冻结产物：panel_manifest.json
- 下游可直接消费的冻结产物：asset_universe_membership.parquet
- 下游可直接消费的冻结产物：cross_section_coverage.parquet
- 下游可直接消费的冻结产物：eligibility_base_mask.parquet
- 下游不得消费 / 重估：未冻结的时序主线信号产物

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
