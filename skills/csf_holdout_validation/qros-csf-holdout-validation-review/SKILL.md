---
name: qros-csf-holdout-validation-review
description: Codex review skill for CSF Holdout Validation stage verification.
---

# CSF Holdout Validation 审查

## 用途

在最后完全未参与设计的窗口里验证冻结方案是否仍然稳定

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

该共享审查协议统一定义：

- adversarial reviewer-agent 合同
- `adversarial_review_request.yaml` / `adversarial_review_result.yaml` / closure artifacts 要求
- `FIX_REQUIRED` 与 closure-ready adverse verdict 语义
- 只有 closure-ready 后才允许运行 `./.qros/bin/qros-review`

## 独立 Review Session 要求

- 本 skill 必须在独立 review session 中执行，不得在当前 author 会话里自动编排 reviewer
- 进入本 skill 后，第一步应在当前 review session **内部**运行 `./.qros/bin/qros-start-review`
- `qros-start-review` 会注册 active review cycle，并写出 `review/request/*`
- review session 只允许读取 `review/request/*` 与 `author/formal/*`
- review session 只允许写入 `review/result/*`
- review session 不得修改 `author/formal/*`
- reviewer 正常只写 `reviewer_findings.raw.yaml`；`./.qros/bin/qros-review` 负责 canonical result、audit 与 closure

## Author Lane 交接前提

- author lane 在发起 review 之前必须先完成 `review-ready` 自查，不要把 reviewer 当成第一轮 artifact completeness checker
- author lane 交给 review session 的 scope 必须是**当前** author outputs，而不是旧 request、旧 digest 或修复前的 stale artifacts
- handoff 必须明确这轮声称已完成的 outputs、希望 reviewer 验证的 formal gate、已知限制 / 未决假设，而不是盲交 reviewer
- 如果上一轮 verdict 是 `FIX_REQUIRED`，author lane 必须先读取 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`，只在 author lane 修复，再由人显式重新启动 review session
- 如果你发现 handoff scope 过期、必需输出缺失、machine-readable artifacts 只是 placeholder，应该明确写成 blocking findings / `FIX_REQUIRED`，而不是替 author lane 猜测或补齐上下文

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

1. 在独立 review session 中，先由本 skill 内部运行 `./.qros/bin/qros-start-review`
2. 再按共享审查协议完成 shared review loop
3. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
4. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
