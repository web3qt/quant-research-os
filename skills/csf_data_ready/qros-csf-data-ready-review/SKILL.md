---
name: qros-csf-data-ready-review
description: Codex review skill for CSF Data Ready stage verification.
---

# CSF Data Ready 审查

## 用途

产出截面因子路线的 date x asset 面板底座、universe membership 和 eligibility mask

## Runtime Stage Admission

开始本 stage-specific review 工作前，必须先在当前 research repo 运行：

`./.qros/bin/qros-check-stage-entry --stage csf_data_ready --lane review`

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

reviewer 写出的 `reviewer_findings.raw.yaml` 必须包含以下顶层字段：

- `review_cycle_id: copy the literal review cycle value printed in the reviewer handoff`
- `reviewer_agent_id: copy the literal reviewer agent id printed in the reviewer handoff`
- `review_loop_outcome: one of FIX_REQUIRED, CLOSURE_READY_PASS, CLOSURE_READY_CONDITIONAL_PASS, CLOSURE_READY_PASS_FOR_RETRY, CLOSURE_READY_RETRY, CLOSURE_READY_NO_GO, CLOSURE_READY_CHILD_LINEAGE`
- `blocking_findings: []`
- `reservation_findings: []`
- `info_findings: []`
- `residual_risks: []`

## 主线程交接前提

- 主线程在发起 review 之前必须先完成 `review-ready` 自查，不要把 reviewer 当成第一轮 artifact completeness checker
- 主线程交给 reviewer 子代理的 scope 必须是**当前** author outputs，而不是旧 request、旧 digest 或修复前的 stale artifacts
- handoff 必须明确这轮声称已完成的 outputs、希望 reviewer 验证的 formal gate、已知限制 / 未决假设，而不是盲交 reviewer
- handoff 必须与 `launcher_review_ready_status`、`launcher_checked_artifact_paths`、`launcher_checked_provenance_paths`、`launcher_handoff_context_paths` 一致
- 如果上一轮 verdict 是 `FIX_REQUIRED`，主线程必须先读取 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`，只在 author lane 修复，再显式重新进入本 stage review skill
- 如果你发现 handoff scope 过期、必需输出缺失、machine-readable artifacts 只是 placeholder，应该明确写成 blocking findings / `FIX_REQUIRED`，而不是替主线程猜测或补齐上下文
- reviewer 不替 runtime 重定义字段；artifact shape 以 `contracts/artifacts/csf_data_ready_artifacts.yaml` 与 deterministic preflight 为准
- 进入 reviewer lane 前必须已经运行 `qros-validate-stage --stage csf_data_ready`，并通过 deterministic preflight
- preflight 中的 `ARTIFACT-CONTRACT-001` 与 `CSF-DATA-SEMANTIC-001` 都是 review 前阻断项
- preflight 覆盖 artifact contract validation、semantic validation 与 upstream binding validation；reviewer 仍需审查机制和残留风险

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
- split_sample_adequacy_report.yaml
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
- train/test/backtest/holdout 每个 split 至少有 1 个 cross_section_snapshot
- 共享字段具备时间语义和缺失语义
- 如允许 group_neutral，taxonomy 已冻结或显式版本化
- run_manifest 已记录 runtime 版本、program_artifacts 和 replay_command
- run_manifest.source_data_provenance 已绑定 real_input、source_data_digest、rows_read、min_ts、max_ts、symbol_count 和 event_count
以下任一情况都不得出现：
- 只有资产时序表，没有显式截面面板合同
- universe membership 无法按日期重建
- eligibility 规则混在下游因子代码里
- split_sample_adequacy_report.yaml 中任一 split 的 cross_section_snapshot 数量低于 minimum_required
- 覆盖率波动显著却没有报告
- 分组中性化需要的 taxonomy 在下游临时补
- 只保存产物，没有 stage-local rebuild 程序或 replay 账本
- source_data_provenance 缺失、为 demo_mode，或无法证明真实输入数据读取规模

## 审查清单

阶段检查项：
- [blocking] 已形成显式的 date x asset 面板合同，而不是零散资产时序表
- [blocking] universe membership 按日期显式记录且可重建
- [blocking] eligibility_base_mask 作为独立底座冻结，未混入后续因子逻辑
- [blocking] 截面覆盖、缺失和共享字段语义已显式记录
- [blocking] train/test/backtest/holdout 每个 split 至少有 1 个 cross_section_snapshot，且 split_sample_adequacy_report final_verdict = PASS
- [blocking] 若后续允许 group_neutral，group taxonomy 已冻结或版本化
- [blocking] artifact catalog 与 field dictionary 已同步登记 CSF 数据底座
- [blocking] run_manifest 已记录 replay_command，且 stage-local rebuild 程序已冻结
- [blocking] run_manifest.source_data_provenance 已绑定真实输入数据；缺 provenance、demo_mode 或 synthetic panel 不得放行
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
- 下游可直接消费的冻结产物：split_sample_adequacy_report.yaml
- 下游可直接消费的冻结产物：eligibility_base_mask.parquet
- 下游不得消费 / 重估：未冻结的时序主线信号产物

## 执行顺序

1. 在当前会话中完成 `review-ready` 自查，并确认 handoff 与 launcher 字段一致
2. 用 `spawn_agent` 创建独立 reviewer 子代理
3. 运行 `./.qros/bin/qros-review-cycle prepare` 写出 active request / handoff / receipt，并复用输出的 reviewer handoff prompt
4. 用 `send_input` 向 reviewer 子代理交付 request / handoff 与本 stage 的 formal gate
5. 等待 reviewer 子代理只写 `review/result/reviewer_findings.raw.yaml`
6. 运行 `./.qros/bin/qros-review` 完成 canonical result、audit 与 closure
7. 再用本 skill 的 formal gate、checklist 和 audit-only 规则解释 stage-specific verdict
8. 若 verdict 需要 rollback 或 downstream 解释，以本文件的 stage-specific 规则为准
