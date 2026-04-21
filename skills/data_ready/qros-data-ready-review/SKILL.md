---
name: qros-data-ready-review
description: Codex review skill for Data Ready stage verification.
---

# Data Ready 审查

## 用途

产出共享、可审计、strategy-agnostic 的 Layer 0 数据基础层

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
- mandate frozen outputs
- 原始市场数据或共享上游数据源
- 正式 universe 与时间边界

## 必需输出

必需输出:
- aligned_bars/
- rolling_stats/
- qc_report.parquet
- dataset_manifest.json
- validation_report.md
- data_contract.md
- dedupe_rule.md
- universe_summary.md
- universe_exclusions.csv
- universe_exclusions.md
- data_ready_gate_decision.md
- run_manifest.json
- rebuild_data_ready.py
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：Data Ready

正式门禁摘要：
必须全部满足：
- 基准腿覆盖审计已完成
- dense 时间轴已生成，正式对象时间轴长度一致
- 缺失、坏价、stale 和 outlier 语义已显式保留
- qc_report 与 dataset_manifest 已生成
- 排除项和准入结果已显式记录
- required_outputs 全部存在，且 machine-readable artifact 都有 companion field documentation
- run_manifest 已记录 runtime 版本、program_artifacts 和 replay_command
以下任一情况都不得出现：
- 没有统一时间栅格
- 混用 open_time 和 close_time 作为主键
- 静默吞掉缺失或静默 forward-fill
- 基准腿覆盖或 universe 审计无法解释
- 只保存产物，没有 stage-local rebuild 程序或 replay 账本

## 审查清单

阶段检查项：
- [blocking] dense 时间轴已生成，目标对象时间栅格一致
- [blocking] 缺失、stale、outlier、坏价等语义被显式标记，而非静默修复
- [blocking] 基准腿（如 BTC）覆盖审计通过
- [blocking] dataset_manifest.json 已冻结当前数据版本、Universe 版本和产物路径
- [blocking] 去重规则与时间主键口径明确，未混用 open_time / close_time
- [blocking] Universe 排除项已显式记录，并给出原因
- [blocking] run_manifest 已记录 replay_command，且 stage-local rebuild 程序已冻结
- [reservation] rolling_stats 或等价可复用 rolling 缓存已生成

## 仅审计项

仅审计项:
- 个别对象质量偏弱但未触发正式排除
- rolling cache 选择是否足够经济

## 本阶段 Rollback 规则

- 默认 rollback stage：data_ready
- 允许修改：数据抽取
- 允许修改：时间对齐
- 允许修改：QC 规则
- 允许修改：admissibility 审计
- 以下情况必须开 child lineage：想修改 mandate 冻结的时间边界
- 以下情况必须开 child lineage：想修改 mandate 冻结的 universe 口径

## 本阶段下游权限

- 可进入下游阶段：signal_ready
- 下游可直接消费的冻结产物：aligned_bars/
- 下游可直接消费的冻结产物：rolling_stats/
- 下游可直接消费的冻结产物：qc_report.parquet
- 下游可直接消费的冻结产物：dataset_manifest.json
- 下游可直接消费的冻结产物：universe_fixed.csv
- 下游不得消费 / 重估：正式时间边界
- 下游不得消费 / 重估：universe admission rules

## 执行顺序

1. 在独立 review session 中，先由本 skill 内部运行 `./.qros/bin/qros-start-review`
2. 再按共享审查协议完成 shared review loop
3. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
4. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
