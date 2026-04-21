---
name: qros-csf-backtest-ready-review
description: Codex review skill for CSF Backtest Ready stage verification.
---

# CSF Backtest Ready 审查

## 用途

将冻结后的因子分数映射成正式组合，并验证成本后的经济可行性

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
- 已冻结的 csf_test_evidence 输出
- portfolio_expression 提案
- cost / capacity 提案

## 必需输出

必需输出:
- portfolio_contract.yaml
- portfolio_weight_panel.parquet
- rebalance_ledger.csv
- turnover_capacity_report.parquet
- cost_assumption_report.md
- engine_compare.csv
- portfolio_summary.parquet
- name_level_metrics.parquet
- drawdown_report.json
- csf_backtest_gate_table.csv
- csf_backtest_contract.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：CSF Backtest Ready

正式门禁摘要：
必须全部满足：
- 只消费 csf_selected_variants_test 中通过的 variants
- 组合规则 machine-readable 冻结
- 成本后结果仍具经济意义
- 换手、容量、参与率分析完整
- 组合结果不是极少数 name 或日期单独支撑
- 组合表达与 mandate 冻结一致
以下任一情况都不得出现：
- backtest 内重新挑选 variant
- 改变 long/short cut 或权重规则却不回退
- 只报 gross，不报 net after cost
- 没有 name-level concentration 诊断
- 容量分析缺失
- 结果只靠单一极端窗口或单一资产支撑

## 审查清单

阶段检查项：
- [blocking] backtest 只消费 test 阶段冻结通过的 variant 与组合规则
- [blocking] portfolio_expression 已冻结且与 factor_role 匹配：standalone_alpha 使用独立组合表达；regime_filter 只允许 target_strategy_filter；combo_filter 只允许 target_strategy_filter / target_strategy_overlay
- [blocking] weight mapping、gross / net exposure、turnover、cost 和 capacity 口径已冻结
- [blocking] 净收益、回撤和资金曲线基于正式资金记账口径
- [blocking] 未在 backtest 中重新挑选 variant、重估权重或改写组合规则
- [blocking] 若为 regime_filter / combo_filter，target strategy compare 与 gated / ungated summary 已一并冻结
- [reservation] name-level concentration、engine compare 和异常收益 sanity check 已保留
- [blocking] mean_net_return <= 0 时不得将 csf_backtest_ready 判为通过

## 仅审计项

仅审计项:
- 组合表达是否足够清晰
- 成本假设是否解释充分

## 本阶段 Rollback 规则

- 默认 rollback stage：csf_backtest_ready
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正组合权重和成本假设
- 以下情况必须开 child lineage：portfolio_expression 大类变化
- 以下情况必须开 child lineage：组合表达从截面切到别的研究问题

## 本阶段下游权限

- 可进入下游阶段：csf_holdout_validation
- 下游可直接消费的冻结产物：portfolio_contract.yaml
- 下游可直接消费的冻结产物：portfolio_weight_panel.parquet
- 下游可直接消费的冻结产物：csf_backtest_gate_table.csv
- 下游不得消费 / 重估：未冻结的权重搜索轨迹

## 执行顺序

1. 在独立 review session 中，先由本 skill 内部运行 `./.qros/bin/qros-start-review`
2. 再按共享审查协议完成 shared review loop
3. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
4. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
