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

## 子代理执行要求

- 本 skill 必须由独立 reviewer 子代理执行，不得由当前 author 线程或启动 review 的主线程直接执行
- 在当前 `Codex-only` 版本里，发起 review 的主线程必须先通过 native `spawn_agent` 启动一个不继承 author 历史的 reviewer 子代理，再由该子代理执行本 skill
- 当前主线程只允许准备 `review/request/*`、等待 reviewer 子代理落 `review/result/*`，不得自己撰写 `adversarial_review_result.yaml` 或 `review_findings.yaml`
- reviewer 子代理只允许读取 `review/request/*` 与 `author/formal/*`
- reviewer 子代理只允许写入 `review/result/*`
- 若没有独立 reviewer 子代理，必须停在 review pending / launch blocked，不得退化成同线程 review

## 主线程交接前提

- 发起 review 的主线程必须先完成 `review-ready` 自查，再把当前 stage 交给 reviewer；不要把 reviewer 当成第一轮 artifact completeness checker
- 主线程交给 reviewer 的 scope 必须是**当前** author outputs，而不是旧 request、旧 digest 或修复前的 stale artifacts
- 主线程必须把这轮声称已完成的 outputs、希望 reviewer 验证的 formal gate、已知限制 / 未决假设写进 handoff context，而不是盲交 reviewer
- 当前 request / handoff 里还必须有 `launcher_review_ready_status`、`launcher_checked_artifact_paths`、`launcher_checked_provenance_paths`、`launcher_handoff_context_paths`
- 如果上一轮 verdict 是 `FIX_REQUIRED`，主线程必须先读取 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`，回 author lane 修复并刷新 outputs，再发起新的 reviewer cycle
- 如果你发现 handoff scope 过期、必需输出缺失、machine-readable artifacts 只是 placeholder，应该明确写成 blocking findings / `FIX_REQUIRED`，而不是替 launcher 猜测或补齐上下文

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

1. 先按共享审查协议完成 shared review loop
2. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
3. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
