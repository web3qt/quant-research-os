---
name: qros-stage-failure-handler
description: Use when qros stage review verdicts are PASS FOR RETRY, RETRY, NO-GO, or CHILD LINEAGE, and the agent must stop normal stage progression and route failure handling by the current failed stage.
---

# QROS Stage Failure Handler

## Purpose

这是 QROS 的统一失败入口 skill。

它只做一件事：

- 当当前谱系在阶段 review 上收到 `PASS FOR RETRY`、`RETRY`、`NO-GO` 或 `CHILD LINEAGE`
- agent 必须 stop normal stage progression
- 然后按当前失败阶段进入对应的机构失败处置协议

失败不是普通 debug。先冻结失败，再分类，再决定是否 `PATCH`、`CONTROLLED_RETRY`、`STAGE_ROLLBACK`、`CHILD_LINEAGE` 或 `NO_GO`。

## Scope

本 skill 只覆盖这些阶段：

- `data_ready`
- `signal_ready`
- `train_freeze`
- `test_evidence`
- `backtest_ready`
- `holdout_validation`
- `shadow`

不覆盖：

- `idea_intake`
- `mandate`
- `promotion_decision`
- `canary_production`

## Entry Conditions

进入本 skill 的条件只有两类：

1. `qros-research-session` 已经报告 `requires_failure_handling = true`
2. 当前 review verdict 明确是：
   - `PASS FOR RETRY`
   - `RETRY`
   - `NO-GO`
   - `CHILD LINEAGE`

一旦满足进入条件，agent 必须：

- 停止正常推进
- 不得继续下一个 `*_confirmation_pending`
- 不得把失败当成普通 review note
- 不得在未冻结失败前直接重写阶段产物

## Shared Failure Harness

无论当前失败阶段是什么，都按这个固定顺序处理：

1. 识别当前失败 stage
2. 读取 `stage_completion_certificate.yaml` 的 review verdict
3. 冻结失败事实和失败证据
4. 读取对应阶段 fail-SOP
5. 读取 `docs/fail-sop/lineage_change_control_sop_cn.md`
6. 判断当前原线是否还能承载修改
7. 形成正式处置方向

默认正式处置方向只能是：

- `PATCH`
- `CONTROLLED_RETRY`
- `STAGE_ROLLBACK`
- `CHILD_LINEAGE`
- `NO_GO`

## Stage Routing

### `data_ready`

读取：

- `docs/fail-sop/01_data_ready_failure_sop_cn.md`

优先检查：

- `DATA_MISSING`
- `DATA_MISALIGNMENT`
- `LEAKAGE_FAIL`
- `QUALITY_FAIL`
- `SCHEMA_FAIL`
- `REPRO_FAIL`
- `SCOPE_FAIL`

### `signal_ready`

读取：

- `docs/fail-sop/02_signal_ready_failure_sop_cn.md`

优先检查：

- 信号语义漂移
- 字段不可复验
- 参数身份漂移
- coverage 或 schema 问题

### `train_freeze`

读取：

- `docs/fail-sop/03_train_freeze_failure_sop_cn.md`

优先检查：

- freeze 缺失
- 后验冻结
- multiple testing
- post-freeze drift
- scope fail

### `test_evidence`

读取：

- `docs/fail-sop/04_test_evidence_failure_sop_cn.md`

优先检查：

- `EVIDENCE_ABSENT`
- `EVIDENCE_FRAGILE`
- `REGIME_SPECIFIC_FAIL`
- `SELECTION_BIAS_FAIL`
- `ARTIFACT_REPRO_FAIL`
- `SCOPE_DRIFT_FAIL`

### `backtest_ready`

读取：

- `docs/fail-sop/05_backtest_failure_sop_cn.md`

优先检查：

- 执行归因
- 成本归因
- 容量问题
- 组合规则一致性
- scope fail

### `holdout_validation`

读取：

- `docs/fail-sop/06_holdout_failure_sop_cn.md`

优先检查：

- purity
- generalization
- selection bias
- scope fail

### `shadow`

读取：

- `docs/fail-sop/07_shadow_failure_sop_cn.md`

优先检查：

- `OPS_FAIL`
- `EXECUTION_FAIL`
- `CAPACITY_FAIL`
- `GENERALIZATION_FAIL`
- `THESIS_FAIL`
- `SCOPE_FAIL`

## Required Outputs

每次 failure handling 至少要形成这些正式产物草案：

- `failure_intake.md`
- `failure_evidence_index.yaml`
- `failure_classification.yaml`
- `failure_disposition.yaml`
- `change_control_decision.yaml`

其中 `failure_disposition.yaml` 至少写清：

- `failed_stage`
- `review_verdict`
- `failure_class`
- `disposition`
- `rollback_stage`
- `allowed_changes`
- `forbidden_changes`
- `next_action`

## Working Rules

- 默认先冻结失败，再解释原因
- 默认不允许恢复正常 stage progression
- 默认不允许跳过 failure disposition
- 默认不允许用失败结果反向重写上游冻结对象
- 如果研究主问题、冻结对象身份或交易语义发生变化，必须升级为 `CHILD_LINEAGE` 或更高等级 change control

## Conversation Contract

进入本 skill 后，agent 的输出顺序必须是：

1. 报告失败 stage 与 review verdict
2. 明确说明主线推进已停止
3. 回显当前阶段 fail-SOP 的检查轴
4. 给出 failure classification 草案
5. 给出正式 disposition 草案
6. 只有在需要治理判断时才问用户

不要把这个 skill 用成：

- 通用 debug 聊天
- 自由 brainstorming
- 对失败结果的事后包装

这是机构失败处置协议，不是普通修错提示。
