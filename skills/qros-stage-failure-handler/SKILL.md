---
name: qros-stage-failure-handler
description: Use when qros stage review verdicts are PASS FOR RETRY, RETRY, NO-GO, or CHILD LINEAGE, and the agent must stop normal stage progression, freeze failure evidence, and route to the appropriate stage-specific failure skill and lineage change control.
---

# QROS Stage Failure Handler（入口路由器）

## Purpose

这是 QROS 的统一失败入口 skill。

职责只有三件事：

1. 识别当前失败 stage 与 review verdict
2. 冻结失败证据（产出入口级产物）
3. 路由到对应阶段 failure skill + `qros-lineage-change-control`

本 skill 是路由器，不是处置器。实际失败分类、triage 步骤、retry 纪律、FAIL-HARD/FAIL-SOFT 判断，均由各阶段 failure skill 完成；change control 判断由 `qros-lineage-change-control` 完成。

## Scope

覆盖阶段：

- `data_ready` → `qros-data-ready-failure`
- `signal_ready` → `qros-signal-ready-failure`
- `train_freeze` → `qros-train-freeze-failure`
- `test_evidence` → `qros-test-evidence-failure`
- `backtest_ready` → `qros-backtest-failure`
- `holdout_validation` → `qros-holdout-failure`
- `shadow` → `qros-shadow-failure`

不覆盖：`idea_intake`、`mandate`、`promotion_decision`、`canary_production`

## Entry Conditions

进入本 skill 的唯一条件：

- 当前 review verdict 明确是：
  - `PASS FOR RETRY`
  - `RETRY`
  - `NO-GO`
  - `CHILD LINEAGE`
- 或 `qros-research-session` 报告 `requires_failure_handling = true`

一旦满足进入条件：

- 停止正常推进
- 不得继续下一个 `*_confirmation_pending`
- 不得把失败当成普通 review note
- 不得在未冻结失败前直接重写阶段产物

## Entry Harness（入口固定步骤）

无论哪个阶段失败，都执行：

### Step 1. 识别失败 stage

从 `stage_completion_certificate.yaml` 读取：

- `stage`
- `review_verdict`
- `reviewer`
- `timestamp`

### Step 2. 冻结入口级失败证据

产出两个入口级产物：

**`failure_intake.md`** 至少包含：

```yaml
lineage_id: <lineage_id>
failed_stage: <stage>
review_verdict: <PASS FOR RETRY | RETRY | NO-GO | CHILD LINEAGE>
reviewer: <reviewer>
timestamp: <timestamp>
summary_of_failure: <1-3句话描述失败现象>
routing_to_stage_skill: <skill_name>
routing_to_change_control: true
```

**`failure_evidence_index.yaml`** 至少包含：

```yaml
failed_stage: <stage>
artifacts_present: []   # 列出当前阶段已存在的产物
artifacts_missing: []   # 列出预期但缺失的产物
stage_completion_certificate: <path>
data_version: <version>
code_version: <commit>
```

### Step 3. 路由

明确宣告：

```
主线推进已停止。
路由到：[stage-specific failure skill]
路由到：qros-lineage-change-control
```

然后按 Stage Routing 表进入对应 skill。

## Stage Routing

| Failed Stage | Route To |
|---|---|
| `data_ready` | `qros-data-ready-failure` |
| `signal_ready` | `qros-signal-ready-failure` |
| `train_freeze` | `qros-train-freeze-failure` |
| `test_evidence` | `qros-test-evidence-failure` |
| `backtest_ready` | `qros-backtest-failure` |
| `holdout_validation` | `qros-holdout-failure` |
| `shadow` | `qros-shadow-failure` |

每个 stage-specific skill 完成 failure classification 后，必须将结论传入 `qros-lineage-change-control` 进行 change control 判定。

## Required Outputs（入口级）

本 skill 只负责产出：

- `failure_intake.md`
- `failure_evidence_index.yaml`

其余所有产物（`failure_classification.yaml`、`failure_disposition.yaml`、`change_control_decision.yaml` 等）由下游 skill 产出。

## Working Rules

- 默认先冻结失败，再解释原因
- 默认不允许恢复正常 stage progression
- 本 skill 不做 failure classification，不做 triage，不做 change control
- 不得把这个 skill 用成通用 debug 聊天或事后包装

## Conversation Contract

进入本 skill 后，输出顺序必须是：

1. 报告 failed stage 与 review verdict
2. 明确说明主线推进已停止
3. 输出 `failure_intake.md` 草案
4. 输出 `failure_evidence_index.yaml` 草案
5. 宣布路由到对应 stage-specific failure skill 与 `qros-lineage-change-control`
