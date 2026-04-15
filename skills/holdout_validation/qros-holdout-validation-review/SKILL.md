---
name: qros-holdout-validation-review
description: Codex review skill for Holdout Validation stage verification.
---

# Holdout Validation 审查

## 用途

用最终未参与设计的窗口验证冻结方案是否没有翻向

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

该共享审查协议统一定义：

- adversarial reviewer-agent 合同
- `adversarial_review_request.yaml` / `adversarial_review_result.yaml` / closure artifacts 要求
- `FIX_REQUIRED` 与 closure-ready adverse verdict 语义
- 只有 closure-ready 后才允许运行 `./.qros/bin/qros-review`

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

## 本阶段 Rollback 规则

- 默认 rollback stage：holdout_validation
- 允许修改：holdout execution rerun
- 允许修改：holdout reporting
- 以下情况必须开 child lineage：想基于 holdout 结果改正式规则

## 本阶段下游权限

- 下游可直接消费的冻结产物：holdout_gate_decision.md
- 下游可直接消费的冻结产物：holdout_backtest_compare.csv
- 下游不得消费 / 重估：any research parameter
- 下游不得消费 / 重估：whitelist
- 下游不得消费 / 重估：best_h

## 执行顺序

1. 先按共享审查协议完成 shared review loop
2. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
3. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
