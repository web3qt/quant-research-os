# Mandate Admission 到 Mandate 的流程

## 目标

QROS 的第一阶段从 `mandate_admission` 开始。它把 raw idea 的资格判断、scope、route assessment 和 kill criteria 统一压进 `01_mandate/author/draft/mandate_admission.yaml`，然后进入 `mandate_freeze_confirmation_pending` 等待用户确认 mandate freeze。

这个流程的边界是：admission 只判断研究是否值得进入正式 mandate，正式下游消费物仍然只来自 `01_mandate/author/formal/`。

## 流程

1. 用户从 `qros-research-session` 提交 raw idea。
2. runtime 创建或恢复 lineage，并 scaffold `01_mandate/author/draft/mandate_admission.yaml` 与 `mandate_freeze_draft.yaml`。
3. agent 逐项问清 observation、primary hypothesis、counter-hypothesis、candidate routes、recommended route、scope、data source、bar size 和 kill criteria。
4. 当 `admission_decision.verdict == ACCEPT_FOR_MANDATE` 且 freeze draft 完整后，session 停在 `mandate_freeze_confirmation_pending`。
5. 用户明确确认 mandate freeze 后，runtime 写入 `01_mandate/author/draft/mandate_transition_approval.yaml`。
6. mandate author lane 生成 `01_mandate/author/formal/*`，然后进入 mandate review。

## Admission 规则

`mandate_admission.yaml` 必须回答这些问题：

- 观测事实是否可研究、可复现、可执行。
- primary hypothesis 和 counter-hypothesis 是否构成真正的机制对立。
- route assessment 是否明确 `candidate_routes`、`recommended_route`、`why_recommended`、`why_not_other_routes` 和 `route_risks`。
- scope 是否明确 market、universe、target task、bar size 和 data source。
- kill criteria 是否不依赖未来实验结果。

admission 通过不等于 mandate 已完成。只有用户确认 freeze，并且 `01_mandate/author/formal/*` 通过 `qros-validate-stage --stage mandate` 与 mandate review 后，mandate 才能作为下游阶段输入。

## Mandate Contract Validation

mandate formal artifacts 的字段真值层是 `contracts/artifacts/mandate_artifacts.yaml`。`qros-mandate-author` 只能把已确认的 admission 与 freeze draft 物化为正式产物，不得自行发明字段或跳过 validation。

最小验证命令：

```bash
qros-validate-stage --stage mandate --lineage-id <lineage_id>
```
