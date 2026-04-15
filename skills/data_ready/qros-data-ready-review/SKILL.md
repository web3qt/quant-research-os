---
name: qros-data-ready-review
description: Codex review skill for Data Ready stage verification.
---

# Data Ready 审查

## 用途

产出共享、可审计、strategy-agnostic 的 Layer 0 数据基础层

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- mandate frozen outputs
- 原始市场数据或共享上游数据源
- 正式 universe 与时间边界

## 必需输出

必需输出:
- aligned_bars/
- rolling_stats/
- qc_report.parquet
- dataset_manifest.json
- validation_report.md
- data_contract.md
- dedupe_rule.md
- universe_summary.md
- universe_exclusions.csv
- universe_exclusions.md
- data_ready_gate_decision.md
- run_manifest.json
- rebuild_data_ready.py
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Data Ready

正式门禁摘要：
必须全部满足：
- 基准腿覆盖审计已完成
- dense 时间轴已生成，正式对象时间轴长度一致
- 缺失、坏价、stale 和 outlier 语义已显式保留
- qc_report 与 dataset_manifest 已生成
- 排除项和准入结果已显式记录
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
- run_manifest 已记录 runtime 版本、program_artifacts 和 replay_command
以下任一情况都不得出现：
- 没有统一时间栅格
- 混用 open_time 和 close_time 作为主键
- 静默吞掉缺失或静默 forward-fill
- 基准腿覆盖或 universe 审计无法解释
- 只保存产物，没有 stage-local rebuild 程序或 replay 账本

## 审查清单

阶段检查项：
- [blocking] dense 时间轴已生成，目标对象时间栅格一致
- [blocking] 缺失、stale、outlier、坏价等语义被显式标记，而非静默修复
- [blocking] 基准腿（如 BTC）覆盖审计通过
- [blocking] dataset_manifest.json 已冻结当前数据版本、Universe 版本和产物路径
- [blocking] 去重规则与时间主键口径明确，未混用 open_time / close_time
- [blocking] Universe 排除项已显式记录，并给出原因
- [blocking] run_manifest 已记录 replay_command，且 stage-local rebuild 程序已冻结
- [reservation] rolling_stats 或等价可复用 rolling 缓存已生成

## 仅审计项

仅审计项:
- 个别对象质量偏弱但未触发正式排除
- rolling cache 选择是否足够经济

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

- 默认 rollback stage：data_ready
- 允许修改：数据抽取
- 允许修改：时间对齐
- 允许修改：QC 规则
- 允许修改：admissibility 审计
- 以下情况必须开 child lineage：想修改 mandate 冻结的时间边界
- 以下情况必须开 child lineage：想修改 mandate 冻结的 universe 口径

## 下游权限

- 可进入下游阶段：signal_ready
- 下游可直接消费的冻结产物：aligned_bars/
- 下游可直接消费的冻结产物：rolling_stats/
- 下游可直接消费的冻结产物：qc_report.parquet
- 下游可直接消费的冻结产物：dataset_manifest.json
- 下游可直接消费的冻结产物：universe_fixed.csv
- 下游不得消费 / 重估：正式时间边界
- 下游不得消费 / 重估：universe admission rules

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
