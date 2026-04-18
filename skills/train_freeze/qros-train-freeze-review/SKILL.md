---
name: qros-train-freeze-review
description: Codex review skill for Train Calibration stage verification.
---

# Train Calibration 审查

## 用途

在训练窗内冻结阈值、regime 切点、质量过滤和参数台账

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
- signal_ready frozen outputs
- mandate time split and parameter grid
- 训练窗定义

## 必需输出

必需输出:
- train_thresholds.json
- train_quality.parquet
- train_param_ledger.csv
- train_rejects.csv
- train_gate_decision.md
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Train Calibration

正式门禁摘要：
必须全部满足：
- 所有训练阈值、regime 切点和辅助条件切点仅使用训练窗估计
- train_param_ledger 和 train_rejects 都已保存
- 保留与拒绝都有明确原因
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
以下任一情况都不得出现：
- 用 test 或 backtest 结果回写 train 阈值
- 只保留通过参数，不保留完整搜索轨迹
- 没有冻结阈值就进入 Test

## 审查清单

阶段检查项：
- [blocking] 训练阈值、分位尺子、regime 切点已冻结
- [blocking] 训练质量过滤已冻结，且未把 test/backtest 信息带入
- [blocking] 完整参数 ledger 已保存
- [blocking] reject ledger 已保存，并可解释拒绝原因
- [blocking] 没有用训练收益最大化直接选最终策略
- [blocking] 未根据 test/backtest 结果回写 train freeze
- [reservation] 若参数粗筛发生，理由仅限排除荒谬区间，而非后验收益优化

## 仅审计项

仅审计项:
- 参数空间是否仍可继续 coarse-to-fine 收窄
- 某些辅助条件切点是否需要在 child lineage 单独升级

## 本阶段 Rollback 规则

- 默认 rollback stage：train_calibration
- 允许修改：train threshold estimation
- 允许修改：quality filters
- 允许修改：ledger generation
- 以下情况必须开 child lineage：借用 test 或 backtest 信息改 train 尺子
- 以下情况必须开 child lineage：引入新的正式机制变量

## 本阶段下游权限

- 可进入下游阶段：test_evidence
- 下游可直接消费的冻结产物：train_thresholds.json
- 下游可直接消费的冻结产物：train_param_ledger.csv
- 下游可直接消费的冻结产物：train_rejects.csv
- 下游不得消费 / 重估：frozen thresholds
- 下游不得消费 / 重估：frozen regime cuts
- 下游不得消费 / 重估：rejected param_id or symbol-param combinations

## 执行顺序

1. 先按共享审查协议完成 shared review loop
2. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
3. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
