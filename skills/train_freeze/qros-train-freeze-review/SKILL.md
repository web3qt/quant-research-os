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
