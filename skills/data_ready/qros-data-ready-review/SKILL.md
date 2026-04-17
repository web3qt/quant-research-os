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

## 子代理执行要求

- 本 skill 必须由独立 reviewer 子代理执行，不得由当前 author 线程或启动 review 的主线程直接执行
- 在当前 `Codex-only` 版本里，发起 review 的主线程必须先通过 native `spawn_agent` 启动一个不继承 author 历史的 reviewer 子代理，再由该子代理执行本 skill
- 当前主线程只允许准备 `review/request/*`、等待 reviewer 子代理落 `review/result/*`，不得自己撰写 `adversarial_review_result.yaml` 或 `review_findings.yaml`
- reviewer 子代理只允许读取 `review/request/*` 与 `author/formal/*`
- reviewer 子代理只允许写入 `review/result/*`
- 若没有独立 reviewer 子代理，必须停在 review pending / launch blocked，不得退化成同线程 review

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

1. 先按共享审查协议完成 shared review loop
2. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
3. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
