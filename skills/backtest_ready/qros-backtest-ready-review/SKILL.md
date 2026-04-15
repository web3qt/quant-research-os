---
name: qros-backtest-ready-review
description: Codex review skill for Backtest Ready stage verification.
---

# Backtest Ready 审查

## 用途

用冻结后的候选集和交易规则验证策略可交易性与正式资金曲线口径

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
- test_evidence frozen_spec.json
- selected_symbols_test.csv or selected_symbols_test.parquet
- frozen signal fields and best_h
- execution, portfolio and risk overlay rules

## 必需输出

必需输出:
- engine_compare.csv
- vectorbt/
- backtrader/
- strategy_combo_ledger.csv
- capacity_review.md
- backtest_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Backtest Ready

正式门禁摘要：
必须全部满足：
- 仅使用上游冻结的 whitelist、best_h 和交易规则身份
- vectorbt 与 backtrader 双引擎正式回测已完成
- 收益、Sharpe、回撤使用正式资金记账口径
- capacity_review 已写清 deployable capital、主要容量瓶颈、自冲击边界和成本吞噬位置
- 若触发 abnormal performance sanity check，则复核已完成且无阻断性问题
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
以下任一情况都不得出现：
- 只跑单一回测引擎就宣布 Backtest Ready
- 在 Backtest 内重新选币或重估 best_h
- 成本、容量或资金记账口径无法解释
- 双引擎存在语义冲突

## 审查清单

阶段检查项：
- [blocking] 输入白名单和交易规则来自上游冻结文件
- [blocking] vectorbt 与 backtrader 两套正式回测均已完成
- [blocking] 双引擎关键结果一致，semantic_gap = false
- [blocking] 收益、回撤和资金曲线基于正式资金记账口径
- [blocking] 未在 backtest 中重新选币或重估 best_h
- [blocking] 若收益异常高，abnormal performance sanity check 已完成
- [reservation] 若搜索多套策略组合，combo ledger 与预算纪律完整
- [reservation] gross / net / fee / turnover / close reason 已拆解解释

## 仅审计项

仅审计项:
- 容量假设的进一步补强
- 更重压力测试
- 主备方案收敛前的非阻断性 reservations

## 本阶段 Rollback 规则

- 默认 rollback stage：backtest_ready
- 允许修改：execution policy
- 允许修改：portfolio policy
- 允许修改：risk overlay
- 允许修改：cost model implementation
- 以下情况必须开 child lineage：想重写 alpha 机制
- 以下情况必须开 child lineage：想回头改 train thresholds 或 test whitelist

## 本阶段下游权限

- 可进入下游阶段：holdout_validation
- 下游可直接消费的冻结产物：selected strategy combo
- 下游可直接消费的冻结产物：backtest frozen config
- 下游可直接消费的冻结产物：engine_compare.csv
- 下游不得消费 / 重估：whitelist
- 下游不得消费 / 重估：best_h
- 下游不得消费 / 重估：core signal thresholds

## 执行顺序

1. 先按共享审查协议完成 shared review loop
2. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
3. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
