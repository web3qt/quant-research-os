---
name: qros-tss-train-freeze-failure
description: Use when failure_class is determined for tss_train_freeze stage on the time_series_signal route and the agent must triage frozen threshold or variant-governance failure without falling back to legacy train_freeze handling.
---

# QROS TSS Train Freeze Failure Handler

## Purpose

本 skill 处置 `tss_train_freeze` 阶段的失败，只适用于 `research_route = time_series_signal`。

由 `qros-stage-failure-handler` 路由触发后执行。本 skill 负责：

1. 读取入口级 `failure_intake.md` 与 `failure_evidence_index.yaml`
2. 判定 TSS train-freeze failure class
3. 冻结 `failure_classification.yaml`
4. 冻结 `failure_disposition.yaml` 或 `post_retry_decision.yaml`
5. 将结论传递给 `qros-lineage-change-control`

不得把 TSS 失败路由到 legacy unprefixed failure skill。

## Stage Boundary

`tss_train_freeze` 的职责是冻结 train window、threshold provenance、candidate variants、kept variants 与 rejected variants。

失败处理只能审计和修复这些冻结对象的治理链，不得根据 test/backtest/holdout 结果回写 threshold、variant set 或 signal family。

## Failure Classes

- `TSS_THRESHOLD_FREEZE_FAIL`: threshold ledger 缺失、不一致或允许 test 重估
- `TSS_VARIANT_GOVERNANCE_FAIL`: candidate/kept/rejected variants 无法追溯或集合关系不合法
- `TSS_TRAIN_SPLIT_DRIFT_FAIL`: train window、time split 或 route inheritance 发生漂移
- `TSS_ARTIFACT_REPRO_FAIL`: `tss_train_freeze.yaml`、ledger 或 provenance 无法复现
- `TSS_SCOPE_DRIFT_FAIL`: train freeze 实质改变了 signal family、horizon 或研究问题

## Triage Sequence

1. 冻结失败现场：确认 failure package id、review verdict、review findings 和当前 `04_tss_train_freeze/author/formal` artifact 列表。
2. 检查 threshold discipline：确认 threshold 只来自 train window，且 downstream 明确禁止 test retuning。
3. 检查 variant governance：确认 `kept_variant_ids` 是 candidate set 子集，reject ledger 解释完整。
4. 检查 upstream binding：确认只消费 `tss_signal_ready` 的冻结 signal/param/horizon。
5. 判定 failure class 与 disposition。

## Required Outputs

写入当前 failure package 目录：

- `failure_classification.yaml`
- `failure_disposition.yaml` 或 `post_retry_decision.yaml`
- `retry_plan.md`（仅当允许受控 retry）

## Allowed Modifications

- 修正 `tss_train_freeze.yaml` 中未冻结或错误记录的 train-only governance 字段
- 补全 `train_threshold_ledger.csv`
- 补全 `train_variant_ledger.csv`
- 补全 `train_variant_rejects.csv`
- 补全 artifact catalog、field dictionary 或 provenance 说明

## Forbidden Modifications

- 用 test/backtest/holdout 结果回写 threshold
- 在 failure handling 中新增未在 signal_ready 冻结的 param_id
- 改写 signal family、horizon 或研究问题
- 绕过 `qros-lineage-change-control`

## Change Control Handoff

完成 classification 后，必须将以下字段传给 `qros-lineage-change-control`：

```yaml
failed_stage: tss_train_freeze
research_route: time_series_signal
failure_class: <class>
disposition: <PASS_FOR_RETRY | RETRY | NO_GO | CHILD_LINEAGE>
rollback_stage: <stage>
allowed_modifications: []
forbidden_modifications: []
```
