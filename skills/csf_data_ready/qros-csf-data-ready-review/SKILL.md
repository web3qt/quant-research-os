---
name: qros-csf-data-ready-review
description: Codex review skill for CSF Data Ready stage verification.
---

# CSF Data Ready 审查

## 用途

产出截面因子路线的 date x asset 面板底座、universe membership 和 eligibility mask

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
- 截面 universe 提案
- 截面共享字段底座提案

## 必需输出

必需输出:
- panel_manifest.json
- asset_universe_membership.parquet
- cross_section_coverage.parquet
- eligibility_base_mask.parquet
- shared_feature_base/
- csf_data_contract.md
- run_manifest.json
- rebuild_csf_data_ready.py
- artifact_catalog.md
- field_dictionary.md

## 正式门禁

阶段：CSF Data Ready

正式门禁摘要：
必须全部满足：
- 面板主键明确且唯一：date + asset
- 截面覆盖可审计
- universe membership 显式记录
- eligibility mask 作为独立底座存在
- 共享字段具备时间语义和缺失语义
- 如允许 group_neutral，taxonomy 已冻结或显式版本化
- run_manifest 已记录 runtime 版本、program_artifacts 和 replay_command
以下任一情况都不得出现：
- 只有资产时序表，没有显式截面面板合同
- universe membership 无法按日期重建
- eligibility 规则混在下游因子代码里
- 覆盖率波动显著却没有报告
- 分组中性化需要的 taxonomy 在下游临时补
- 只保存产物，没有 stage-local rebuild 程序或 replay 账本

## 审查清单

阶段检查项：
- [blocking] 已形成显式的 date x asset 面板合同，而不是零散资产时序表
- [blocking] universe membership 按日期显式记录且可重建
- [blocking] eligibility_base_mask 作为独立底座冻结，未混入后续因子逻辑
- [blocking] 截面覆盖、缺失和共享字段语义已显式记录
- [blocking] 若后续允许 group_neutral，group taxonomy 已冻结或版本化
- [blocking] artifact catalog 与 field dictionary 已同步登记 CSF 数据底座
- [blocking] run_manifest 已记录 replay_command，且 stage-local rebuild 程序已冻结
- [reservation] 覆盖率波动、边缘样本或 taxonomy 版本切换均已明确记录在审查材料中
- [blocking] panel_primary_key、cross_section_time_key、asset_key 与 shared_feature_outputs 均已显式冻结，不能保持空缺
- [blocking] asset_universe_membership 非空，且 eligibility_base_mask 在 (date, asset) 上唯一

## 仅审计项

仅审计项:
- 面板字段命名是否清楚
- 共享字段说明是否便于 reviewer 追踪

## 本阶段 Rollback 规则

- 默认 rollback stage：csf_data_ready
- 允许修改：澄清文档表述
- 允许修改：补全缺失 artifact
- 允许修改：修正截面面板主键与 membership 规则
- 以下情况必须开 child lineage：面板主键改变
- 以下情况必须开 child lineage：universe 改变
- 以下情况必须开 child lineage：eligibility 语义改变

## 本阶段下游权限

- 可进入下游阶段：csf_signal_ready
- 下游可直接消费的冻结产物：panel_manifest.json
- 下游可直接消费的冻结产物：asset_universe_membership.parquet
- 下游可直接消费的冻结产物：cross_section_coverage.parquet
- 下游可直接消费的冻结产物：eligibility_base_mask.parquet
- 下游不得消费 / 重估：未冻结的时序主线信号产物

## 执行顺序

1. 先按共享审查协议完成 shared review loop
2. 再用本 skill 的 formal gate、checklist 和 audit-only 规则做 stage-specific 判定
3. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
