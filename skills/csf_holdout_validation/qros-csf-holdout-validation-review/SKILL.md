---
name: qros-csf-holdout-validation-review
description: Codex review skill for CSF Holdout Validation stage verification.
---

# CSF Holdout Validation 审查

## 用途

在最后完全未参与设计的窗口里验证冻结方案是否仍然稳定

## Runtime Stage Admission

开始本 stage-specific review 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage csf_holdout_validation --lane review`

若命令失败，必须停止；不得继续 review，不得启动 reviewer，不得运行 `qros-review-cycle prepare`。按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state 后再重进本 skill。

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

该共享审查协议统一定义：

- adversarial reviewer-agent 合同
- `adversarial_review_request.yaml` / `adversarial_review_result.yaml` / closure artifacts 要求
- `FIX_REQUIRED` 与 closure-ready adverse verdict 语义
- 只有 closure-ready 后才允许运行 `./.qros/bin/qros-review`

## 独立 reviewer 子代理要求

- 本 skill 是用户显式进入的 stage-specific review 入口；不再要求你手动再开一个独立 review session
- 进入本 skill 后，必须在**当前会话**里用 `spawn_agent` 拉起独立 reviewer 子代理，且 `fork_context` 必须是 `false`
- 先用一个最小初始化消息创建 reviewer 子代理，要求它先等待 binding / handoff，不要在 receipt 写出前擅自写文件
- reviewer 子代理创建后，主线程优先运行 `./.qros/bin/qros-review-cycle prepare --reviewer-agent-id <child_agent_id> --reviewer-id <reviewer_identity> --reviewer-session-id <child_agent_id> --host codex`
- `qros-review-cycle prepare` 负责注册 active review cycle，写出 `review/request/*` 与 `reviewer_receipt.yaml`，并输出 reviewer handoff prompt 与 closer command
- 主线程随后必须用 `send_input` 把 request / handoff manifest / stage-specific gate 交给 reviewer 子代理
- reviewer 子代理只允许读取 `review/request/*` 与 `author/formal/*`
- reviewer 子代理只允许写入 `review/result/reviewer_findings.raw.yaml`
- reviewer 子代理不得修改 `author/formal/*`
- reviewer 子代理完成后，主线程必须运行 `./.qros/bin/qros-review`；它负责 canonical result、audit 与 closure

## 主线程交接前提

- 主线程在发起 review 之前必须先完成 `review-ready` 自查，不要把 reviewer 当成第一轮 artifact completeness checker
- 主线程交给 reviewer 子代理的 scope 必须是**当前** author outputs，而不是旧 request、旧 digest 或修复前的 stale artifacts
- handoff 必须明确这轮声称已完成的 outputs、希望 reviewer 验证的 formal gate、已知限制 / 未决假设，而不是盲交 reviewer
- handoff 必须与 `launcher_review_ready_status`、`launcher_checked_artifact_paths`、`launcher_checked_provenance_paths`、`launcher_handoff_context_paths` 一致
- 如果上一轮 verdict 是 `FIX_REQUIRED`，主线程必须先读取 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`，只在 author lane 修复，再显式重新进入本 stage review skill
- 如果你发现 handoff scope 过期、必需输出缺失、machine-readable artifacts 只是 placeholder，应该明确写成 blocking findings / `FIX_REQUIRED`，而不是替主线程猜测或补齐上下文
- reviewer 不替 runtime 重定义字段；artifact shape 以 `contracts/artifacts/csf_holdout_validation_artifacts.yaml` 与 deterministic preflight 为准
- 进入 reviewer lane 前必须已经运行 `qros-validate-stage --stage csf_holdout_validation`，并通过 deterministic preflight
- preflight 中的 `ARTIFACT-CONTRACT-001` 与 `CSF-HOLDOUT-SEMANTIC-001` 都是 review 前阻断项
- preflight 覆盖 artifact contract validation、semantic validation 与 upstream binding validation；reviewer 仍需审查机制和残留风险

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- 已冻结的 csf_backtest_ready 输出
- 最终 holdout 窗口
- regime shift 审计提案

## 必需输出

必需输出:
- csf_holdout_run_manifest.json
- holdout_factor_diagnostics.parquet
- holdout_test_compare.parquet
- holdout_portfolio_compare.parquet
- rolling_holdout_stability.json
- regime_shift_audit.json
- csf_holdout_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：CSF Holdout Validation

正式门禁摘要：
必须全部满足：
- 只复用冻结方案，不重估上游尺子
- 主要方向未翻向
- 退化可解释且未超过容忍边界
- holdout 覆盖和 breadth 未塌到不可解释
- regime shift 明显时，必须显式审计
以下任一情况都不得出现：
- 在 holdout 调参
- 在 holdout 改 bucket cut、neutralization、weight mapping
- 主要证据翻向
- 结果只靠极少数窗口支撑
- regime shift 明显却没有审计结论

## 审查清单

阶段检查项：
- [blocking] holdout 只复用冻结方案，不重新调参或改写组合规则
- [blocking] holdout_factor_diagnostics 已记录 coverage、breadth、方向一致性和分桶稳定性
- [blocking] holdout_test_compare 与 holdout_portfolio_compare 已生成
- [blocking] regime_shift_audit 已明确记录是否存在显著结构迁移
- [blocking] 未在 holdout 中回写 train/test/backtest 的任何冻结对象
- [blocking] 若主要证据退化，已区分 regime mismatch、样本问题和机制断裂
- [reservation] 最终 holdout 结论、残留风险和后续 lineage 建议均已写明
- [blocking] direction_match = false 或 holdout_mean_net_return <= 0 时不得将 holdout 判为通过

## 仅审计项

仅审计项:
- holdout 文字总结是否清楚
- regime shift 解释是否足够完整

## 本阶段 Rollback 规则

- 默认 rollback stage：csf_holdout_validation
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正 holdout 审计说明
- 以下情况必须开 child lineage：holdout 表明研究语义已改变
- 以下情况必须开 child lineage：regime shift 解释要求重设研究问题

## 本阶段下游权限

- 下游可直接消费的冻结产物：csf_holdout_gate_decision.md
- 下游可直接消费的冻结产物：regime_shift_audit.json
- 下游不得消费 / 重估：未冻结的 holdout 调参结果

## 执行顺序

1. 在当前会话中完成 `review-ready` 自查，并确认 handoff 与 launcher 字段一致
2. 用 `spawn_agent` 创建独立 reviewer 子代理
3. 运行 `./.qros/bin/qros-review-cycle prepare` 写出 active request / handoff / receipt，并复用输出的 reviewer handoff prompt
4. 用 `send_input` 向 reviewer 子代理交付 request / handoff 与本 stage 的 formal gate
5. 等待 reviewer 子代理只写 `review/result/reviewer_findings.raw.yaml`
6. 运行 `./.qros/bin/qros-review` 完成 canonical result、audit 与 closure
7. 再用本 skill 的 formal gate、checklist 和 audit-only 规则解释 stage-specific verdict
8. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
