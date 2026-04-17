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

## 子代理执行要求

- 本 skill 必须由独立 reviewer 子代理执行，不得由当前 author 线程或启动 review 的主线程直接执行
- 在当前 `Codex-only` 版本里，发起 review 的主线程必须先通过 native `spawn_agent` 启动一个不继承 author 历史的 reviewer 子代理，再由该子代理执行本 skill
- 当前主线程只允许准备 `review/request/*`、等待 reviewer 子代理落 `review/result/*`，不得自己撰写 `adversarial_review_result.yaml` 或 `review_findings.yaml`
- reviewer 子代理只允许读取 `review/request/*` 与 `author/formal/*`
- reviewer 子代理只允许写入 `review/result/*`
- 若没有独立 reviewer 子代理，必须停在 review pending / launch blocked，不得退化成同线程 review

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

1. 先按共享审查协议完成 shared review loop
2. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
3. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
