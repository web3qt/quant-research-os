---
name: qros-tss-test-evidence-failure
description: Use when failure_class is determined for tss_test_evidence stage on the time_series_signal route and the agent must triage independent test evidence, split proof, threshold reuse, or selected-variant membership failure.
---

# QROS TSS Test Evidence Failure Handler

## Purpose

本 skill 处置 `tss_test_evidence` 阶段的失败，只适用于 `research_route = time_series_signal`。

由 `qros-stage-failure-handler` 路由触发后执行。本 skill 负责：

1. 读取入口级 `failure_intake.md` 与 `failure_evidence_index.yaml`
2. 判定 TSS test-evidence failure class
3. 冻结 `failure_classification.yaml`
4. 冻结 `failure_disposition.yaml` 或 `post_retry_decision.yaml`
5. 将结论传递给 `qros-lineage-change-control`

不得把 TSS 失败路由到 legacy unprefixed failure skill。

## Stage Boundary

`tss_test_evidence` 的职责是在独立 test window 上验证冻结 TSS variants 的事件路径和 base-rate 差异。

失败处理不得在 test 阶段新增 variants、重估 threshold、重切 split、改写 signal family，或用后续 backtest/holdout 曲线替代 test evidence。

## Failure Classes

- `TSS_SPLIT_PROOF_FAIL`: `split_threshold_attestation.yaml` 缺失、过期或无法证明 test window 独立
- `TSS_THRESHOLD_REUSE_FAIL`: threshold provenance 缺失，或 test 期间发生 retuning
- `TSS_MEMBERSHIP_PROOF_FAIL`: selected variants 无法证明来自 train kept set
- `TSS_UPSTREAM_BINDING_FAIL`: `upstream_binding_digest_ledger.yaml` 缺失、stale、路径漂移或 digest 不匹配
- `TSS_EVIDENCE_ABSENT`: test evidence 不支持方向/path claim
- `TSS_EVIDENCE_FRAGILE`: 证据由极少事件、单一 regime 或少数 variant 支撑
- `TSS_ARTIFACT_REPRO_FAIL`: event returns、gate table 或 summary 无法复现
- `TSS_SCOPE_DRIFT_FAIL`: test evidence 实质改变 signal family、horizon 或研究问题

## Triage Sequence

1. 冻结失败现场：确认 failure package id、review verdict、review findings 和当前 `05_tss_test_evidence/author/formal` artifact 列表。
2. 优先检查 split/threshold proof：若无法证明独立 test 和 no retuning，直接归类为 proof failure。
3. 检查 membership proof：确认所有 selected variants 均来自 train-freeze kept variants。
4. 检查 upstream binding digest ledger：确认 train freeze、time split 和 upstream review closure 绑定未漂移。
5. 检查 evidence quality：确认事件数、base rate 对照、方向一致性和 regime concentration。
6. 判定 failure class 与 disposition。

## Required Outputs

写入当前 failure package 目录：

- `failure_classification.yaml`
- `failure_disposition.yaml` 或 `post_retry_decision.yaml`
- `retry_plan.md`（仅当允许受控 retry）

## Allowed Modifications

- 补全或修正 `split_threshold_attestation.yaml`
- 补全或修正 `selected_variant_membership_proof.csv`
- 补全或修正 `upstream_binding_digest_ledger.yaml`
- 修正当前 stage 的 artifact catalog、field dictionary 或 provenance 说明
- 在不改变 split、threshold、selected variant 集合的前提下重建损坏的 machine artifact

## Forbidden Modifications

- 在 test 中新增未冻结 variant
- 用 test 结果重估 threshold 或修改 train kept set
- 重切 train/test split
- 用 backtest/holdout 曲线替代 test evidence
- 绕过 `qros-lineage-change-control`

## Change Control Handoff

完成 classification 后，必须将以下字段传给 `qros-lineage-change-control`：

```yaml
failed_stage: tss_test_evidence
research_route: time_series_signal
failure_class: <class>
disposition: <PASS_FOR_RETRY | RETRY | NO_GO | CHILD_LINEAGE>
rollback_stage: <stage>
allowed_modifications: []
forbidden_modifications: []
```
