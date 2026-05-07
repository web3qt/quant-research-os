---
name: qros-csf-backtest-ready-review
description: Codex review skill for CSF Backtest Ready stage verification.
---

# CSF Backtest Ready 审查

## 用途

将冻结后的因子分数映射成正式组合，并验证成本后的经济可行性

## Runtime Stage Admission

开始本 stage-specific review 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage csf_backtest_ready --lane review`

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
- reviewer 不替 runtime 重定义字段；artifact shape 以 `contracts/artifacts/csf_backtest_ready_artifacts.yaml` 与 deterministic preflight 为准
- 进入 reviewer lane 前必须已经运行 `qros-validate-stage --stage csf_backtest_ready`，并通过 deterministic preflight
- preflight 中的 `ARTIFACT-CONTRACT-001` 与 `CSF-BACKTEST-SEMANTIC-001` 都是 review 前阻断项
- preflight 覆盖 artifact contract validation、semantic validation 与 upstream binding validation；reviewer 仍需审查机制和残留风险

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
- portfolio_summary.parquet
- name_level_metrics.parquet
- drawdown_report.json
- target_strategy_compare.parquet
- csf_backtest_gate_table.csv
- csf_backtest_contract.md
- csf_backtest_gate_decision.md
- run_manifest.json
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
- [reservation] name-level concentration、target strategy compare 和异常收益 sanity check 已保留
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

1. 在当前会话中完成 `review-ready` 自查，并确认 handoff 与 launcher 字段一致
2. 用 `spawn_agent` 创建独立 reviewer 子代理
3. 运行 `./.qros/bin/qros-review-cycle prepare` 写出 active request / handoff / receipt，并复用输出的 reviewer handoff prompt
4. 用 `send_input` 向 reviewer 子代理交付 request / handoff 与本 stage 的 formal gate
5. 等待 reviewer 子代理只写 `review/result/reviewer_findings.raw.yaml`
6. 运行 `./.qros/bin/qros-review` 完成 canonical result、audit 与 closure
7. 再用本 skill 的 formal gate、checklist 和 audit-only 规则解释 stage-specific verdict
8. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
