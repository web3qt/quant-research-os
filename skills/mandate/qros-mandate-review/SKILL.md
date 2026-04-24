---
name: qros-mandate-review
description: Codex review skill for Mandate stage verification.
---

# Mandate 审查

## 用途

冻结研究主问题、时间边界、universe、字段层级和参数边界

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

该共享审查协议统一定义：

- adversarial reviewer-agent 合同
- `adversarial_review_request.yaml` / `adversarial_review_result.yaml` / closure artifacts 要求
- `FIX_REQUIRED` 与 closure-ready adverse verdict 语义
- 只有 closure-ready 后才允许运行 `./.qros/bin/qros-review`

## 独立 reviewer 子代理要求

- 本 skill 是用户显式进入的 stage-specific review 入口；不再要求你手动再开一个独立 review session / Codex review session
- 进入本 skill 后，必须在**当前会话**里用 `spawn_agent` 拉起独立 reviewer 子代理，且 `fork_context` 必须是 `false`
- 先用一个最小初始化消息创建 reviewer 子代理，要求它先等待 binding / handoff，不要在 receipt 写出前擅自写文件
- reviewer 子代理创建后，主线程优先运行 `./.qros/bin/qros-review-cycle prepare --spawned-agent-id <child_agent_id> --reviewer-id <reviewer_identity> --reviewer-session-id <child_agent_id>`
- `qros-review-cycle prepare` 负责注册 active review cycle，写出 `review/request/*` 与 `spawned_reviewer_receipt.yaml`，并输出 reviewer handoff prompt 与 closer command
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
- 进入 reviewer lane 前必须先完成 deterministic review-ready 自查；若 preflight 有 blocking finding，必须先修 author outputs。

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- 研究主题说明或专题草稿
- 候选 universe 与时间边界提案
- 字段族、公式模板、实现栈和并行计划提案

## 必需输出

必需输出:
- mandate.md
- research_scope.md
- time_split.json
- parameter_grid.yaml
- run_config.toml
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Mandate

正式门禁摘要：
必须全部满足：
- 研究主问题与明确禁止事项已冻结
- 正式时间窗、切分方式、time label 和 no-lookahead 约定已冻结
- 正式 universe、准入口径和字段分层已冻结
- 参数字典、公式模板、实现栈、parallelization_plan 和 non_rust_exceptions 已写清
- 后续 crowding distinctiveness review 的比较基准，以及 capacity review 的流动性代理、参与率边界和自冲击假设边界已写清
- required_outputs 全部存在，且 machine-readable artifact 都能追到 companion field documentation
以下任一情况都不得出现：
- required_outputs 缺失
- 时间窗、universe 或无前视边界未冻结
- 只有裸字段名或裸参数名，没有字段解释和参数字典
- 研究问题被后验结果倒逼修改但没有重置 mandate

## 审查清单

阶段检查项：
- [blocking] 研究主问题已冻结，且明确写清不研究什么
- [blocking] 正式时间窗与 Train/Test/Backtest/Holdout 切分已冻结
- [blocking] Universe、准入口径、主副腿角色已冻结
- [blocking] 字段分层已写清，且关键字段具有人类可读解释
- [blocking] 信号表达式模板、时间语义和无前视约定已写清
- [blocking] 参数字典、参数候选集、参数约束已写清
- [reservation] 实现栈、并行计划、非 Rust 例外说明已记录
- [blocking] 若关键字段或参数仅列名称未解释，则不得通过
- [blocking] 若 research_route = cross_sectional_factor，则 factor_role、factor_structure、portfolio_expression、neutralization_policy 已冻结；且 non-standalone 需要 target_strategy_reference，group_neutral 需要 group_taxonomy_reference

## 仅审计项

仅审计项:
- 专题样板写法是否足够清楚
- 字段命名是否优雅或便于新成员阅读

## 本阶段 Rollback 规则

- 默认 rollback stage：mandate
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正字段解释、参数字典和目录契约
- 以下情况必须开 child lineage：主问题改变
- 以下情况必须开 child lineage：universe 改变
- 以下情况必须开 child lineage：time split 改变
- 以下情况必须开 child lineage：机制模板改变

## 本阶段下游权限

- 可进入下游阶段：data_ready
- 可进入下游阶段：csf_data_ready
- 下游可直接消费的冻结产物：time_split.json
- 下游可直接消费的冻结产物：parameter_grid.yaml
- 下游可直接消费的冻结产物：run_config.toml
- 下游不得消费 / 重估：test results
- 下游不得消费 / 重估：backtest results
- 下游不得消费 / 重估：holdout results

## 执行顺序

1. 在当前会话中完成 `review-ready` 自查，并确认 handoff 与 launcher 字段一致
2. 用 `spawn_agent` 创建独立 reviewer 子代理
3. 运行 `./.qros/bin/qros-review-cycle prepare` 写出 active request / handoff / receipt，并复用输出的 reviewer handoff prompt
4. 用 `send_input` 向 reviewer 子代理交付 request / handoff 与本 stage 的 formal gate
5. 等待 reviewer 子代理只写 `review/result/reviewer_findings.raw.yaml`
6. 运行 `./.qros/bin/qros-review` 完成 canonical result、audit 与 closure
7. 再用本 skill 的 formal gate、checklist 和 audit-only 规则解释 stage-specific verdict
8. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
