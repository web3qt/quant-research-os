---
name: qros-signal-ready-review
description: Codex review skill for Signal Ready stage verification.
---

# Signal Ready 审查

## 用途

把 mandate 已冻结的表达式模板实例化成统一 schema 的正式信号层

## 共享审查协议

执行本 stage review 前，必须先阅读并遵守 `docs/guides/qros-review-shared-protocol.md`。

该共享审查协议统一定义：

- adversarial reviewer-agent 合同
- `adversarial_review_request.yaml` / `adversarial_review_result.yaml` / closure artifacts 要求
- `FIX_REQUIRED` 与 closure-ready adverse verdict 语义
- 只有 closure-ready 后才允许运行 `./.qros/bin/qros-review`

## 独立 reviewer 子代理要求

- 本 skill 是用户显式进入的 stage-specific review 入口；不再要求你手动再开一个 Codex review session
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

## 共用输入

- `contracts/stages/workflow_stage_gates.yaml`
- `contracts/review/review_checklist_master.yaml`
- `artifact_catalog.md`
- `field_dictionary.md` or `*_fields.md`
- `run_manifest.json`

## 必需输入

必需输入:
- mandate frozen outputs
- data_ready frozen outputs
- 已冻结的 signal expression template

## 必需输出

必需输出:
- param_manifest.csv
- params/
- signal_coverage.csv
- signal_coverage.md
- signal_coverage_summary.md
- signal_contract.md
- signal_fields_contract.md
- signal_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Signal Ready

正式门禁摘要：
必须全部满足：
- 已显式物化 baseline 或 declared search_batch 的全部 param_id
- param_id 身份清晰且有 param_manifest
- 正式 timeseries schema、参数元数据和时间语义已冻结
- signal gate 文档已生成
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
以下任一情况都不得出现：
- baseline 或 required param_id 物化失败
- failed symbols 或 failed params 大于零
- 下游才发现 signal contract 缺失或字段越层
- 在 Train 阶段才首次引入未曾在 Signal Ready 物化过的 param_id

## 审查清单

阶段检查项：
- [blocking] 信号字段合同已生成，字段 schema 固定
- [blocking] param_id 身份已显式落地，并存在 param manifest
- [blocking] timeseries 已落盘，且下游无需临时重算同名信号
- [blocking] 当前阶段引用了上游 Mandate 的表达式模板，而未静默改写机制
- [blocking] 未越权做白名单结论、收益结论或 test/backtest 级别结论
- [reservation] coverage / low_sample / pair_missing 等最小质量保留项已审计
- [blocking] Train 阶段只能消费已在本阶段显式物化过的 param_id

## 仅审计项

仅审计项:
- finite coverage、low_sample_rate、pair_missing_rate 等质量摘要
- search batch 中非阻断性的稀疏参数组

## 本阶段 Rollback 规则

- 默认 rollback stage：signal_ready
- 允许修改：signal 实现
- 允许修改：字段命名
- 允许修改：标签对齐
- 允许修改：companion docs
- 以下情况必须开 child lineage：改变信号机制模板
- 以下情况必须开 child lineage：改变字段分层边界

## 本阶段下游权限

- 可进入下游阶段：train_calibration
- 下游可直接消费的冻结产物：param_manifest.csv
- 下游可直接消费的冻结产物：params/
- 下游可直接消费的冻结产物：signal_coverage.csv
- 下游可直接消费的冻结产物：signal_fields_contract.md
- 下游不得消费 / 重估：signal definition
- 下游不得消费 / 重估：param identity space

## 执行顺序

1. 在当前会话中完成 `review-ready` 自查，并确认 handoff 与 launcher 字段一致
2. 用 `spawn_agent` 创建独立 reviewer 子代理
3. 运行 `./.qros/bin/qros-review-cycle prepare` 写出 active request / handoff / receipt，并复用输出的 reviewer handoff prompt
4. 用 `send_input` 向 reviewer 子代理交付 request / handoff 与本 stage 的 formal gate
5. 等待 reviewer 子代理只写 `review/result/reviewer_findings.raw.yaml`
6. 运行 `./.qros/bin/qros-review` 完成 canonical result、audit 与 closure
7. 再用本 skill 的 formal gate、checklist 和 audit-only 规则解释 stage-specific verdict
8. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
