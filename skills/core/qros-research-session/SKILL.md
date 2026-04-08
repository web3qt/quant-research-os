---
name: qros-research-session
description: Use when the user wants to start one orchestrated QROS conversation that drives idea_intake, mandate authoring, mandate review, data_ready authoring, data_ready review, signal_ready authoring, signal_ready review, train_freeze authoring/review, test_evidence authoring/review, backtest_ready authoring/review, holdout_validation authoring/review, and the cross_sectional_factor branch from a single entry point.
---

# QROS Research Session

## Purpose

这是 QROS 的统一入口 skill。

目标不是让用户记住多个 skills 和脚本，而是：

- 从一个会话开始
- 自动识别或创建 lineage
- 自动判断当前 stage
- 对每个 major stage 显式推进 `content-confirm -> author -> review-confirm -> review -> mandatory-display -> next-stage-confirm`
- 在 mainline 中，review 完成后不再直接跳入下一个 `*_confirmation_pending`；必须先经过当前 stage 的 mandatory display，再进入 `*_next_stage_confirmation_pending`
- 在 `research_route = cross_sectional_factor` 时，mandate review 完成后同样先走 mandate 的 mandatory display / next-stage gates，再切入 `csf_data_ready_confirmation_pending`
- 只在缺关键信息或治理分歧时停下来问用户

## First-Wave Scope

第一版只覆盖：

- `idea_intake`
- `idea_intake_confirmation_pending`
- `mandate`
- `mandate review`
- `data_ready`
- `data_ready review`
- `signal_ready`
- `signal_ready review`
- `train_freeze`
- `train_freeze review`
- `test_evidence`
- `test_evidence review`
- `backtest_ready`
- `backtest_ready review`
- `holdout_validation`
- `holdout_validation review`

在 `research_route = cross_sectional_factor` 时，第一版还覆盖：

- `csf_data_ready`
- `csf_data_ready review`
- `csf_signal_ready`
- `csf_signal_ready review`
- `csf_train_freeze`
- `csf_train_freeze review`
- `csf_test_evidence`
- `csf_test_evidence review`
- `csf_backtest_ready`
- `csf_backtest_ready review`
- `csf_holdout_validation`
- `csf_holdout_validation review`

明确不覆盖：

- `promotion_decision`
- `shadow_admission`
- `canary_production`

## Required Runtime

Use the orchestrator runtime:

- `~/.qros/bin/qros-session --raw-idea "<idea>"`
- `~/.qros/bin/qros-session --lineage-id "<lineage_id>"`

Reuse the deterministic runtime rather than improvising directory state in chat.

The user should not need to remember internal commands. Runtime commands are backend mechanics for the agent, debugging, and manual recovery.

QROS repo is the workflow package. The actual lineage artifacts must be written in the user's active research repo. Do not treat framework-repo placeholders, empty directories, or contract-only docs as if they were completed research outputs.

## CSF Route Branch

When `research_route = cross_sectional_factor`, do not continue to use the default stage contract as if it were a time-series route.

After mandate review closure, do **not** jump directly into CSF data-ready authoring. Mandatory display must run first, then next-stage confirmation, and only after that should the session switch to the independent CSF chain:

- `csf_data_ready_confirmation_pending`
- `csf_data_ready`
- `csf_data_ready review`
- `csf_signal_ready_confirmation_pending`
- `csf_signal_ready`
- `csf_signal_ready review`
- `csf_train_freeze_confirmation_pending`
- `csf_train_freeze`
- `csf_train_freeze review`
- `csf_test_evidence_confirmation_pending`
- `csf_test_evidence`
- `csf_test_evidence review`
- `csf_backtest_ready_confirmation_pending`
- `csf_backtest_ready`
- `csf_backtest_ready review`
- `csf_holdout_validation_confirmation_pending`
- `csf_holdout_validation`
- `csf_holdout_validation review`

Use the CSF-specific grouped confirmations and ask for these frozen contract groups in order:

- `panel_contract`
- `quality_semantics`
- `universe_admission`
- `shared_derived_layer`
- `delivery_contract`
- `factor_identity`
- `factor_role_contract`
- `factor_structure_contract`
- `neutralization_policy`
- `preprocess_contract`
- `neutralization_contract`
- `ranking_bucket_contract`
- `rebalance_contract`
- `window_contract`
- `formal_gate_contract`
- `admissibility_contract`
- `audit_contract`
- `execution_policy`
- `portfolio_policy`
- `risk_overlay`
- `engine_contract`
- `reuse_contract`
- `drift_audit`
- `failure_governance`

## Failure Routing

Review failure is not ordinary debugging.

When runtime status reports `requires_failure_handling = true`, the current conversation must switch into `qros-stage-failure-handler`.

The automatic failure-routing trigger verdicts are:

- `PASS FOR RETRY`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`

When any of those verdicts appear for the current reviewed stage, the agent must:

- stop normal stage progression
- not enter the next `*_confirmation_pending`
- not continue ordinary authoring for the same stage
- reuse runtime failure-routing status instead of ad hoc judgment
- follow `qros-stage-failure-handler` before any further stage edits

## Working Rules

1. Resolve or create the lineage
2. Detect the current stage from disk
3. Auto-scaffold `00_idea_intake/` when it does not exist
4. Drive `idea_intake` authoring with the same discipline as `qros-idea-intake-author`
5. 对于一个全新的 raw idea，必须先停在 `idea_intake_confirmation_pending`，不得把用户第一句话直接当成完整 qualification 结论
6. 如果当前入口是 `raw_idea` 且没有显式 `lineage_id`，不得无声恢复另一条旧 lineage；只有用户明确给出 `lineage_id` 或明确表达“继续那条线”时，才允许 resume
6. 先显式确认 `observation`
7. 再显式确认 `primary hypothesis` 与 `counter-hypothesis`
8. 再显式确认 `candidate_routes`、`recommended_route`、`route_risks`
9. 再显式确认 `market`、`universe`、`target_task`
10. 再显式确认 `data_source` 与 `bar_size`
11. 再显式确认 `kill criteria` 或 `reframe` 条件
12. 在这些 intake 关键项没有得到用户回答前，不得静默填写完整 `qualification_scorecard.yaml` 或直接给出 `GO_TO_MANDATE`
13. Only after the intake interview is explicitly confirmed may the agent internally write the equivalent of `CONFIRM_IDEA_INTAKE`
14. If the intake gate reaches `GO_TO_MANDATE`, stop at `mandate_confirmation_pending`
15. Start a grouped mandate freeze conversation instead of silently writing `01_mandate`
16. Confirm `research_intent`
17. 在 `research_intent` 中确认 `route_assessment`、`research_route`、`excluded_routes`
18. Confirm `scope_contract`
19. Confirm `data_contract`, especially 数据来源哪里来 and what `bar_size` is frozen, for example `1m`, `5m`, or `15m`
20. Confirm `execution_contract`
21. Show one final mandate summary
22. Ask the user one explicit question: `是否确认进入 mandate？`
23. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_MANDATE` and freeze mandate artifacts
24. Drive mandate completion with the same discipline as `qros-mandate-author`
25. When mandate artifacts are ready, stop at `mandate_review_confirmation_pending`
26. Only after explicit review confirmation may the session enter `mandate_review`
27. After mandate review closure, run mandatory display automatically, then enter `mandate_next_stage_confirmation_pending`, and only then enter `data_ready_confirmation_pending`
28. Confirm `extraction_contract`
29. Confirm `quality_semantics`
30. Confirm `universe_admission`
31. Confirm `shared_derived_layer`
32. Confirm `delivery_contract`
33. For `data_ready`, ensure the active research repo actually materializes dense aligned data, shared caches, and QC or coverage evidence required by the stage contract
34. Never treat empty directories, placeholder files, or contract-only markdown as sufficient `data_ready` completion
35. Show one final data_ready summary
36. Ask the user one explicit question: `是否按以上内容冻结 data_ready？`
37. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_DATA_READY` and freeze data_ready artifacts
38. Drive data_ready completion with the same discipline as `qros-data-ready-author`
39. When data_ready artifacts are ready, stop at `data_ready_review_confirmation_pending`
40. Only after explicit review confirmation may the session enter `data_ready_review`
41. After data_ready review closure, run mandatory display automatically, then enter `data_ready_next_stage_confirmation_pending`; `Data Ready Reflection` only appears after successful display generation
42. Confirm `signal_expression`
43. Confirm `param_identity`
44. Confirm `time_semantics`
45. Confirm `signal_schema`
46. Confirm `delivery_contract`
47. For `signal_ready`, ensure the active research repo actually materializes baseline signal timeseries, param manifests and coverage evidence required by the stage contract
48. Never treat empty directories, placeholder files, or contract-only markdown as sufficient `signal_ready` completion
49. Show one final signal_ready summary
50. Ask the user one explicit question: `是否按以上内容冻结 signal_ready？`
51. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_SIGNAL_READY` and freeze signal_ready artifacts
52. Drive signal_ready completion with the same discipline as `qros-signal-ready-author`
53. When signal_ready artifacts are ready, move into signal_ready review
54. Reuse the same gate discipline as `qros-signal-ready-review`
55. After `signal_ready review` closure, enter `train_freeze_confirmation_pending`
56. Confirm `window_contract`
57. Confirm `threshold_contract`
58. Confirm `quality_filters`
59. Confirm `param_governance`
60. Confirm `delivery_contract`
61. For `train_freeze`, ensure the active research repo actually materializes train thresholds, quality evidence and param ledgers required by the stage contract
62. Never treat empty directories, placeholder files, or contract-only markdown as sufficient `train_freeze` completion
63. Show one final train_freeze summary
64. Ask the user one explicit question: `是否按以上内容冻结 train_freeze？`
65. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_TRAIN_FREEZE` and freeze train artifacts
66. Drive train_freeze completion with the same discipline as `qros-train-freeze-author`
67. When train_freeze artifacts are ready, move into train_freeze review
68. Reuse the same gate discipline as `qros-train-freeze-review`
69. After `train_freeze review` closure, enter `test_evidence_confirmation_pending`
70. Confirm `window_contract`
71. Confirm `formal_gate_contract`
72. Confirm `admissibility_contract`
73. Confirm `audit_contract`
74. Confirm `delivery_contract`
75. For `test_evidence`, ensure the active research repo actually materializes independent-sample statistics, admissibility outputs and frozen selection artifacts required by the stage contract
76. Never treat empty directories, placeholder files, or contract-only markdown as sufficient `test_evidence` completion
77. Show one final test_evidence summary
78. Ask the user one explicit question: `是否按以上内容冻结 test_evidence？`
79. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_TEST_EVIDENCE` and freeze test_evidence artifacts
80. Drive test_evidence completion with the same discipline as `qros-test-evidence-author`
81. When test_evidence artifacts are ready, move into test_evidence review
82. Reuse the same gate discipline as `qros-test-evidence-review`
83. After `test_evidence review` closure, enter `backtest_ready_confirmation_pending`
84. Confirm `execution_policy`
85. Confirm `portfolio_policy`
86. Confirm `risk_overlay`
87. Confirm `engine_contract`
88. Confirm `delivery_contract`
89. For `backtest_ready`, ensure the active research repo actually materializes dual-engine backtest outputs, combo ledgers and capacity evidence required by the stage contract
90. Never treat empty directories, placeholder files, or contract-only markdown as sufficient `backtest_ready` completion
91. Show one final backtest_ready summary
92. Ask the user one explicit question: `是否按以上内容冻结 backtest_ready？`
93. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_BACKTEST_READY` and freeze backtest_ready artifacts
94. Drive backtest_ready completion with the same discipline as `qros-backtest-ready-author`
95. When backtest_ready artifacts are ready, move into backtest_ready review
96. Reuse the same gate discipline as `qros-backtest-ready-review`
97. After `backtest_ready review` closure, enter `holdout_validation_confirmation_pending`
98. Confirm `window_contract`
99. Confirm `reuse_contract`
100. Confirm `drift_audit`
101. Confirm `failure_governance`
102. Confirm `delivery_contract`
103. For `holdout_validation`, ensure the active research repo actually materializes single-window, merged-window and comparison outputs required by the stage contract
104. Never treat empty directories, placeholder files, or contract-only markdown as sufficient `holdout_validation` completion
105. Show one final holdout_validation summary
106. Ask the user one explicit question: `是否按以上内容冻结 holdout_validation？`
107. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_HOLDOUT_VALIDATION` and freeze holdout_validation artifacts
108. Drive holdout_validation completion with the same discipline as `qros-holdout-validation-author`
109. When holdout_validation artifacts are ready, move into holdout_validation review
110. Reuse the same gate discipline as `qros-holdout-validation-review`
111. Stop after `holdout_validation review`; do not silently enter `promotion_decision`

## Auto vs Ask

Auto-act when:

- creating a lineage slug
- scaffolding `00_idea_intake/`
- detecting the current stage
- reporting current state
- when the stage is `csf_data_ready_author`, all freeze groups are already confirmed, and the only remaining blocker is a missing lineage-local stage program, auto-materialize the first-pass runnable program and continue

Ask the user only when:

- key research scope is missing
- counter-hypothesis is missing
- kill criteria are missing
- intake should become `NEEDS_REFRAME` or `DROP`
- a governance judgment must be made explicitly, especially `CONFIRM_MANDATE`, `CONFIRM_DATA_READY`, `CONFIRM_SIGNAL_READY`, `HOLD`, or `REFRAME`

If runtime status reports `requires_failure_handling = true`, do not keep following the normal authoring or review path in this skill. Switch to `qros-stage-failure-handler` immediately.

When the stage is `idea_intake`, the agent must ask explicitly before writing a real qualification verdict:

- `observation` 到底是什么？
- `primary hypothesis` 是什么？
- `counter-hypothesis` 是什么？
- `market`、`universe`、`target_task` 是什么？
- `data_source` 和 `bar_size` 是什么？
- `kill criteria` 或 `reframe` 条件是什么？

Do not treat the user's first raw-idea sentence as if all of these were already confirmed. Do not silently jump from a raw idea to a completed intake gate.

When the stage is `idea_intake_confirmation_pending`, the agent must ask one explicit question after回显 intake summary:

- `是否确认以上 intake 访谈内容，可以进入正式 qualification？`

Do not write a real gate verdict before this explicit confirmation.

When the stage is `mandate_confirmation_pending`, the agent must ask explicitly:

- `research_intent` 这一组冻结什么？
- `scope_contract` 这一组冻结什么？
- `data_contract` 这一组冻结什么？这里必须明确数据来源和 `bar_size`
- `execution_contract` 这一组冻结什么？
- 每组回显当前 freeze draft，并单独确认
- `是否确认进入 mandate？`

Do not skip this question. Do not imply the transition already happened.

When the stage is `data_ready_confirmation_pending`, the agent must ask explicitly:

- `extraction_contract` 这一组冻结什么？
- `quality_semantics` 这一组冻结什么？
- `universe_admission` 这一组冻结什么？
- `shared_derived_layer` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 dense data、rolling caches、QC/coverage artifacts？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 data_ready？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `data_ready`.

When the stage is `signal_ready_confirmation_pending`, the agent must ask explicitly:

- `signal_expression` 这一组冻结什么？
- `param_identity` 这一组冻结什么？
- `time_semantics` 这一组冻结什么？
- `signal_schema` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 signal timeseries、param manifests、coverage artifacts？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 signal_ready？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `signal_ready`.

When the stage is `train_freeze_confirmation_pending`, the agent must ask explicitly:

- `window_contract` 这一组冻结什么？
- `threshold_contract` 这一组冻结什么？
- `quality_filters` 这一组冻结什么？
- `param_governance` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 thresholds、quality artifacts、param ledgers？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 train_freeze？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `train_freeze`.

When the stage is `test_evidence_confirmation_pending`, the agent must ask explicitly:

- `window_contract` 这一组冻结什么？
- `formal_gate_contract` 这一组冻结什么？
- `admissibility_contract` 这一组冻结什么？
- `audit_contract` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 test statistics、admissibility outputs、frozen selection artifacts？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 test_evidence？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `test_evidence`.

When the stage is `backtest_ready_confirmation_pending`, the agent must ask explicitly:

- `execution_policy` 这一组冻结什么？
- `portfolio_policy` 这一组冻结什么？
- `risk_overlay` 这一组冻结什么？
- `engine_contract` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 dual-engine outputs、combo ledgers、capacity artifacts？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 backtest_ready？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `backtest_ready`.

When the stage is `holdout_validation_confirmation_pending`, the agent must ask explicitly:

- `window_contract` 这一组冻结什么？
- `reuse_contract` 这一组冻结什么？
- `drift_audit` 这一组冻结什么？
- `failure_governance` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 single-window、merged-window、comparison artifacts？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 holdout_validation？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `holdout_validation`.

When `research_route = cross_sectional_factor` and the stage is `csf_data_ready_confirmation_pending`, the agent must ask explicitly:

- `panel_contract` 这一组冻结什么？
- `quality_semantics` 这一组冻结什么？
- `universe_admission` 这一组冻结什么？
- `shared_derived_layer` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 panel manifests、coverage artifacts、shared feature layers？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 csf_data_ready？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `csf_data_ready`.

When `research_route = cross_sectional_factor` and the stage is `csf_signal_ready_confirmation_pending`, the agent must ask explicitly:

- `factor_identity` 这一组冻结什么？
- `factor_role_contract` 这一组冻结什么？
- `factor_structure_contract` 这一组冻结什么？
- `neutralization_policy` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 factor panels、factor manifests、coverage artifacts？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 csf_signal_ready？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `csf_signal_ready`.

When `research_route = cross_sectional_factor` and the stage is `csf_train_freeze_confirmation_pending`, the agent must ask explicitly:

- `preprocess_contract` 这一组冻结什么？
- `neutralization_contract` 这一组冻结什么？
- `ranking_bucket_contract` 这一组冻结什么？
- `rebalance_contract` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- `csf_signal_ready` 冻结后，哪些轴不再允许作为 train variants 继续搜索？
- 当前 research repo 里将真实生成哪些 train rules、quality artifacts、variant ledgers？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 csf_train_freeze？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `csf_train_freeze`.

When `research_route = cross_sectional_factor` and the stage is `csf_test_evidence_confirmation_pending`, the agent must ask explicitly:

- `window_contract` 这一组冻结什么？
- `formal_gate_contract` 这一组冻结什么？
- `admissibility_contract` 这一组冻结什么？
- `audit_contract` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 factor statistics、admissibility outputs、frozen selection artifacts？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 csf_test_evidence？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `csf_test_evidence`.

When `research_route = cross_sectional_factor` and the stage is `csf_backtest_ready_confirmation_pending`, the agent must ask explicitly:

- `execution_policy` 这一组冻结什么？
- `portfolio_policy` 这一组冻结什么？
- `risk_overlay` 这一组冻结什么？
- `engine_contract` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 portfolio outputs、combo ledgers、capacity artifacts？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 csf_backtest_ready？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `csf_backtest_ready`.

When `research_route = cross_sectional_factor` and the stage is `csf_holdout_validation_confirmation_pending`, the agent must ask explicitly:

- `window_contract` 这一组冻结什么？
- `reuse_contract` 这一组冻结什么？
- `drift_audit` 这一组冻结什么？
- `failure_governance` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 single-window、merged-window、comparison artifacts？
- 每组回显当前 freeze draft，并单独确认
- `是否按以上内容冻结 csf_holdout_validation？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `csf_holdout_validation`.

## State Source Of Truth

Use disk artifacts as the primary state:

- `outputs/<lineage>/00_idea_intake/`
- `outputs/<lineage>/01_mandate/`
- `outputs/<lineage>/02_data_ready/`
- `outputs/<lineage>/03_signal_ready/`
- `outputs/<lineage>/04_train_freeze/`
- `outputs/<lineage>/05_test_evidence/`
- `outputs/<lineage>/06_backtest/`
- `outputs/<lineage>/07_holdout/`
- `outputs/<lineage>/02_csf_data_ready/`
- `outputs/<lineage>/03_csf_signal_ready/`
- `outputs/<lineage>/04_csf_train_freeze/`
- `outputs/<lineage>/05_csf_test_evidence/`
- `outputs/<lineage>/06_csf_backtest_ready/`
- `outputs/<lineage>/07_csf_holdout_validation/`
- mandate review closure artifacts
- data_ready review closure artifacts
- signal_ready review closure artifacts
- train_freeze review closure artifacts
- test_evidence review closure artifacts
- backtest_ready review closure artifacts
- holdout_validation review closure artifacts
- csf_data_ready review closure artifacts
- csf_signal_ready review closure artifacts
- csf_train_freeze review closure artifacts
- csf_test_evidence review closure artifacts
- csf_backtest_ready review closure artifacts
- csf_holdout_validation review closure artifacts

Do not rely on chat history alone to determine progress.

## Status Reporting

After each meaningful step, report:

- `lineage`
- `current_stage`
- `artifacts_written`
- `gate_status`
- `next_action`
- `why_now`
- `open_risks`

## Guardrails

- Do not fabricate `review_findings.yaml`
- Do not bypass `idea_gate_decision.yaml`
- Do not bypass `mandate_transition_approval.yaml`
- Do not bypass `data_ready_transition_approval.yaml`
- Do not bypass `signal_ready_transition_approval.yaml`
- Do not bypass mandate review closure
- Do not bypass data_ready review closure
- Do not bypass signal_ready review closure
- Do not bypass train_freeze transition approval
- Do not bypass train_freeze review closure
- Do not bypass test_evidence transition approval
- Do not bypass test_evidence review closure
- Do not bypass backtest_ready transition approval
- Do not bypass backtest_ready review closure
- Do not bypass holdout_validation transition approval
- Do not bypass holdout_validation review closure
- Do not bypass csf_data_ready review closure
- Do not bypass csf_signal_ready review closure
- Do not bypass csf_train_freeze review closure
- Do not bypass csf_test_evidence review closure
- Do not bypass csf_backtest_ready review closure
- Do not bypass csf_holdout_validation review closure
- Do not require the user to type backend flags or internal runtime commands during the primary chat workflow

## Internal Discipline Sources

When writing or reviewing content, follow the same contracts as:

- `qros-idea-intake-author`
- `qros-mandate-author`
- `qros-mandate-review`
- `qros-data-ready-author`
- `qros-data-ready-review`
- `qros-signal-ready-author`
- `qros-signal-ready-review`
- `qros-train-freeze-author`
- `qros-train-freeze-review`
- `qros-test-evidence-author`
- `qros-test-evidence-review`
- `qros-backtest-ready-author`
- `qros-backtest-ready-review`
- `qros-holdout-validation-author`
- `qros-holdout-validation-review`
- `qros-csf-data-ready-author`
- `qros-csf-data-ready-review`
- `qros-csf-signal-ready-author`
- `qros-csf-signal-ready-review`
- `qros-csf-train-freeze-author`
- `qros-csf-train-freeze-review`
- `qros-csf-test-evidence-author`
- `qros-csf-test-evidence-review`
- `qros-csf-backtest-ready-author`
- `qros-csf-backtest-ready-review`
- `qros-csf-holdout-validation-author`
- `qros-csf-holdout-validation-review`
