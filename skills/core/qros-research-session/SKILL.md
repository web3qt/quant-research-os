---
name: qros-research-session
description: Use when the user wants one orchestrated QROS conversation from idea_intake through mandate, time_series_signal TSS stages, or cross_sectional_factor CSF stages.
---

# QROS Research Session

## Purpose

这是 QROS 的统一入口 skill。

目标不是让用户记住多个 skills 和脚本，而是：

- 从一个会话开始
- 自动识别或创建 lineage
- 自动判断当前 stage
- 对每个 major stage 显式推进 `content-confirm -> author -> review-confirm -> review -> next-stage-confirm`
- `display` 现在是用户显式触发的 guidance，不是强制阶段，也不是 major stage 自动推进门
- 只在缺关键信息或治理分歧时停下来问用户

## First-Wave Scope

第一版只覆盖：

- `idea_intake`
- `idea_intake_confirmation_pending`
- `mandate`
- `mandate review`
- `tss_data_ready`
- `tss_data_ready review`
- `tss_signal_ready`
- `tss_signal_ready review`
- `tss_train_freeze`
- `tss_train_freeze review`
- `tss_test_evidence`
- `tss_test_evidence review`
- `tss_backtest_ready`
- `tss_backtest_ready review`
- `tss_holdout_validation`
- `tss_holdout_validation review`

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

`tss_holdout_validation review` 或 `csf_holdout_validation review` 是当前单入口编排的终点。

## Required Runtime

用户在 Codex 里应该使用 `$qros-research-session`、`$qros-progress`、`$qros-stage-display` 或对应 `$qros-*-review` 入口，不要让用户直接执行底层脚本。

Use the orchestrator runtime:

- `./.qros/bin/qros-session --raw-idea "<idea>"`
- `./.qros/bin/qros-session --lineage-id "<lineage_id>"`

Reuse the deterministic runtime rather than improvising directory state in chat.

The user should not need to remember internal commands. Runtime commands are backend mechanics for the agent, debugging, and manual recovery.

QROS repo is the workflow package. The actual lineage artifacts must be written in the user's active research repo. Do not treat framework-repo placeholders, empty directories, or contract-only docs as if they were completed research outputs.

## Stage-Specific Entry Discipline

- `qros-research-session` 是普通阶段推进的唯一总控入口；stage-specific author/review skill 只能在 runtime `current_stage` 已经匹配时接手
- 进入任何 stage-specific author skill 前，必须先运行 `./.qros/bin/qros-check-stage-entry --stage <stage_id> --lane author`
- 进入任何 stage-specific review skill 前，必须先运行 `./.qros/bin/qros-check-stage-entry --stage <stage_id> --lane review`
- guard 失败时，不得继续 authoring、不得起 reviewer、不得运行 `qros-review-cycle prepare`；按输出中的 `qros-research-session --lineage-id ...` 恢复 runtime state
- 这层 guard 专门防止 `current_stage` 仍停在上游 handoff、review confirmation 或 next-stage confirmation 时，agent 直接跳到下游 stage-specific skill

## TSS Route Branch

When `research_route = time_series_signal`, use the TSS branch. TSS 是“单个资产用自己的历史预测自己的未来路径/方向”，不是横截面排序；不得把 Rank IC / Top-Bottom / bucket monotonicity 当作 TSS 主证据。

After mandate review closure, do **not** continue into the legacy unprefixed post-mandate mainline as the canonical route. Next-stage confirmation must happen first, and only after that should the session switch to the independent TSS chain:

- `tss_data_ready_confirmation_pending`
- `tss_data_ready`
- `tss_data_ready review`
- `tss_signal_ready_confirmation_pending`
- `tss_signal_ready`
- `tss_signal_ready review`
- `tss_train_freeze_confirmation_pending`
- `tss_train_freeze`
- `tss_train_freeze review`
- `tss_test_evidence_confirmation_pending`
- `tss_test_evidence`
- `tss_test_evidence review`
- `tss_backtest_ready_confirmation_pending`
- `tss_backtest_ready`
- `tss_backtest_ready review`
- `tss_holdout_validation_confirmation_pending`
- `tss_holdout_validation`
- `tss_holdout_validation review`

Use the TSS-specific grouped confirmations and ask for these frozen contract groups in order:

- `extraction_contract`
- `quality_semantics`
- `universe_admission`
- `shared_derived_layer`
- `delivery_contract`
- `signal_expression`
- `param_identity`
- `time_semantics`
- `signal_schema`
- `window_contract`
- `threshold_contract`
- `quality_filters`
- `param_governance`
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

## CSF Route Branch

When `research_route = cross_sectional_factor`, do not continue to use the default stage contract as if it were a time-series route.

After mandate review closure, do **not** jump directly into CSF data-ready authoring. Next-stage confirmation must happen first, and only after that should the session switch to the independent CSF chain:

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

When runtime status reports `blocking_reason_code = FAILURE_DISPOSITION_REQUIRED`, the current conversation must not resume review or next-stage progression. The agent must record a formal `failure_disposition.yaml` in the latest failure package with `decision: NO_GO` or `decision: CHILD_LINEAGE`.

When runtime status reports `blocking_reason_code = FAILURE_DISPOSITION_RECORDED`, the original lineage remains blocked from ordinary review or next-stage progression. Continue only through `qros-lineage-change-control` or a child lineage path.

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

## Language Discipline

- 统一遵守 `docs/guides/qros-authoring-language-discipline.md`，不要在本 skill 内再发明例外语言口径。

## Review Discipline

- author 主会话不得自动编排 reviewer；review 必须由人显式进入对应的 `qros-*-review` skill 发起
- 当前主会话只推进到 `*_review_confirmation_pending`，并在 `review-ready` 自查通过后停住
- 进入 stage-specific review skill 后，当前会话必须用 `spawn_agent` 拉起**独立 reviewer 子代理**
- 当前会话随后必须优先运行 `./.qros/bin/qros-review-cycle prepare` 注册 active review cycle、写出 `review/request/*`，并复用它输出的 reviewer handoff prompt / closer command
- reviewer 子代理只允许读取 `review/request/*` 与 `author/formal/*`
- reviewer 子代理只允许写入 `review/result/reviewer_findings.raw.yaml`
- reviewer 子代理不得修改 `author/formal/*`
- 当前主线程不得自己撰写 `review/result/adversarial_review_result.yaml` 或 `review/result/review_findings.yaml`
- reviewer 正常只写 `reviewer_findings.raw.yaml`
- `./.qros/bin/qros-review` 是唯一 deterministic closer；它负责 canonical result、write-scope audit 和 closure

## Main-Agent Review Loop

- 在 author lane 交给独立 reviewer 子代理之前，主 Agent 必须先做一次 `review-ready` 自查；不要把 reviewer 当成第一轮缺件检查器
- `review-ready` 自查至少覆盖：当前 stage 必需 outputs、`artifact_catalog.md`、`field_dictionary.md`、`run_manifest.json`、当前 stage program provenance，以及 machine-readable artifacts 可读取且不是 placeholder
- 当前 runtime 只在 `mandate_review_confirmation_pending` 强制跑 deterministic review-entry preflight；这是 mandate-first / mandate-only rollout truth，对 reviewer lane 来说不是 optional check，而是进入 review 前的 mandatory reviewer-lane gate
- 对其余 post-mandate `*_review_confirmation_pending`，当前 runtime 还没有统一强制这道 deterministic preflight；主 Agent 仍必须完成 `review-ready` 自查与 handoff 准备，但不要宣称这些阶段已经全量接入同一条 reviewer-lane gate
- 发起 review 前，主 Agent 必须明确 handoff：这轮声称已完成的 outputs、希望 reviewer 验证的 formal gate、已知限制 / 未决假设 / 重点风险；不得盲交 reviewer
- 当前 request / handoff 里还必须冻结 `launcher_review_ready_status`、`launcher_checked_artifact_paths`、`launcher_checked_provenance_paths`、`launcher_handoff_context_paths`
- 当前 request 还会拆分 `stage_content_*` 与 `upstream_binding_*` scope：reviewer 只负责 stage-local 内容审查；上游绑定由 deterministic validator 负责
- 一个 active review cycle 只允许一个 reviewer child；旧 cycle 未解决前，不得再并发起第二个 reviewer child
- 若 `review_loop_outcome = FIX_REQUIRED`，主 Agent 必须先阅读 `review/result/adversarial_review_result.yaml` 与 `review/result/review_findings.yaml`，回 author lane 修复，再刷新 `author/formal/*` 与 request scope 后由人显式重新进入对应 `qros-*-review` skill
- author outputs 一旦变化，旧的 receipt / result / audit 就只能当历史记录，不能继续拿来证明新的 author outputs

## Working Rules

1. Resolve or create the lineage
2. Detect the current stage from disk
3. Auto-scaffold `00_idea_intake/` when it does not exist
4. For `idea_intake`, artifact shape 以 contract 为准：`contracts/artifacts/idea_intake_artifacts.yaml`
5. After scaffold or before attempting `GO_TO_MANDATE`, run `qros-validate-stage --stage idea_intake`; if it fails, fix the artifact shape before continuing
6. Drive `idea_intake` authoring with the same discipline as `qros-idea-intake-author`
7. 对于一个全新的 raw idea，必须先停在 `idea_intake_confirmation_pending`，不得把用户第一句话直接当成完整 qualification 结论
8. 如果当前入口是 `raw_idea` 且没有显式 `lineage_id`，不得无声恢复另一条旧 lineage；只有用户明确给出 `lineage_id` 或明确表达“继续那条线”时，才允许 resume
9. 先显式确认 `observation`
10. 再显式确认 `primary hypothesis` 与 `counter-hypothesis`
11. 再显式确认 `candidate_routes`、`recommended_route`、`route_risks`
12. 再显式确认 `market`、`universe`、`target_task`
13. 再显式确认 `data_source` 与 `bar_size`
14. 再显式确认 `kill criteria` 或 `reframe` 条件
15. 在这些 intake 关键项没有得到用户回答前，不得静默填写完整 `qualification_scorecard.yaml` 或直接给出 `GO_TO_MANDATE`
16. Only after the intake interview is explicitly confirmed may the agent internally write the equivalent of `CONFIRM_IDEA_INTAKE`
17. If the intake gate reaches `GO_TO_MANDATE`, stop at `mandate_confirmation_pending`
18. Start a grouped mandate freeze conversation instead of silently writing `01_mandate`
19. Confirm `research_intent`
20. 在 `research_intent` 中确认 `route_assessment`、`research_route`、`excluded_routes`
21. Confirm `scope_contract`
22. Confirm `data_contract`, especially 数据来源哪里来 and what `bar_size` is frozen, for example `1m`, `5m`, or `15m`
23. Confirm `execution_contract`
24. Show one final mandate summary
25. Ask the user one explicit question: `是否确认进入 mandate？`
26. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_MANDATE` and freeze mandate artifacts
27. Drive mandate completion with the same discipline as `qros-mandate-author`
28. When mandate artifacts are ready, stop at `mandate_review_confirmation_pending`
29. 当 artifacts 已 review-ready 时，主会话停在 `mandate_review_confirmation_pending`，不得自动进入 `mandate_review`
30. 在任何 stage 到达 `*_review_confirmation_pending` 时，先完成 Main-Agent Review Loop 里的 `review-ready` 自查与 handoff 准备，再由人显式进入对应 `qros-*-review` skill
31. Confirm `extraction_contract`
32. Confirm `quality_semantics`
33. Confirm `universe_admission`
34. Confirm `shared_derived_layer`
35. Confirm `delivery_contract`
36. For `data_ready`, ensure the active research repo actually materializes dense aligned data, shared caches, and QC or coverage evidence required by the stage contract
37. Never treat empty directories, placeholder files, or contract-only markdown as sufficient `data_ready` completion
38. Show one final data_ready summary
39. Ask the user one explicit question: `是否按以上内容冻结 data_ready？`
40. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_DATA_READY` and freeze data_ready artifacts
41. Drive data_ready completion with the same discipline as `qros-data-ready-author`
42. When data_ready artifacts are ready, stop at `data_ready_review_confirmation_pending`
43. 当 artifacts 已 review-ready 时，主会话停在 `data_ready_review_confirmation_pending`，不得自动进入 `data_ready_review`
44. 若 review verdict 是 `FIX_REQUIRED`，必须显式回 author lane 修复并刷新 `author/formal/*`，再由人显式重新进入对应 `qros-*-review` skill
45. Confirm `signal_expression`
46. Confirm `param_identity`
47. Confirm `time_semantics`
48. Confirm `signal_schema`
49. Confirm `delivery_contract`
50. For `signal_ready`, ensure the active research repo actually materializes baseline signal timeseries, param manifests and coverage evidence required by the stage contract
48. Never treat empty directories, placeholder files, or contract-only markdown as sufficient `signal_ready` completion
49. Show one final signal_ready summary
50. Ask the user one explicit question: `是否按以上内容冻结 signal_ready？`
51. Only after a clear affirmative reply may the agent internally write the equivalent of `CONFIRM_SIGNAL_READY` and freeze signal_ready artifacts
52. Drive signal_ready completion with the same discipline as `qros-signal-ready-author`
53. When signal_ready artifacts are ready, move into signal_ready review
54. Reuse the same gate discipline as `qros-signal-ready-review`
55. 在 `signal_ready review` 中不得复用上一轮 stale receipt / result；author outputs 变化后必须重开 review cycle
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
83. 在 `test_evidence review` 里若 reviewer 指出缺 artifact / stale scope，主 Agent 必须先修正 handoff 与 formal outputs，再重新提交 review
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
97. 在 `backtest_ready review` 与 `holdout_validation review` 里，主 Agent 只在已经能清楚说明“这轮 reviewer 该审什么”时才允许发起 review
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
111. Stop after `holdout_validation review`; treat it as the terminal stage for the current single-entry flow

## Auto vs Ask

Auto-act when:

- creating a lineage slug
- scaffolding `00_idea_intake/`
- detecting the current stage
- reporting current state
- when a post-mandate author stage reports that the only remaining blocker is a missing lineage-local stage program, stop the normal flow and require Codex to explicitly author or refresh the lineage-local stage program in the current research repo; there is no silent auto-materialize path

Ask the user only when:

- key research scope is missing
- counter-hypothesis is missing
- kill criteria are missing
- intake should become `NEEDS_REFRAME` or `DROP`
- a governance judgment must be made explicitly, especially `CONFIRM_MANDATE`, `CONFIRM_DATA_READY`, `CONFIRM_SIGNAL_READY`, `HOLD`, or `REFRAME`

If runtime status reports `requires_failure_handling = true`, do not keep following the normal authoring or review path in this skill. Switch to `qros-stage-failure-handler` immediately.

For any `*_confirmation_pending` freeze gate, runtime status may expose `freeze_groups` for every group in the current draft. The agent may show all groups in one response. If the user replies `确认全部`, run `./.qros/bin/qros-session --lineage-id <lineage_id> --confirm-all-freeze-groups`; this only marks the current draft groups confirmed and never replaces the final stage approval such as `--confirm-mandate`, `--confirm-data-ready`, or `--confirm-signal-ready`. Do not bulk-confirm unless the current turn or the immediately preceding user-visible summary showed every group draft being confirmed.

When `research_route = time_series_signal` and the stage is `tss_data_ready_confirmation_pending`, the agent must ask explicitly:

- `extraction_contract` 这一组冻结什么？
- `quality_semantics` 这一组冻结什么？
- `universe_admission` 这一组冻结什么？
- `shared_derived_layer` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 time index、quality flags、split adequacy 和 TSS data artifacts？
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
- `是否按以上内容冻结 tss_data_ready？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `tss_data_ready`.

When `research_route = time_series_signal` and the stage is `tss_signal_ready_confirmation_pending`, the agent must ask explicitly:

- `signal_expression` 这一组冻结什么？
- `param_identity` 这一组冻结什么？
- `time_semantics` 这一组冻结什么？
- `signal_schema` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 signal panels、event panels、param manifests、route inheritance artifacts？
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
- `是否按以上内容冻结 tss_signal_ready？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `tss_signal_ready`.

When `research_route = time_series_signal` and the stage is `tss_train_freeze_confirmation_pending`, the agent must ask explicitly:

- `window_contract` 这一组冻结什么？
- `threshold_contract` 这一组冻结什么？
- `quality_filters` 这一组冻结什么？
- `param_governance` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 thresholds、variant ledgers、reject ledgers、quality artifacts？
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
- `是否按以上内容冻结 tss_train_freeze？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `tss_train_freeze`.

When `research_route = time_series_signal` and the stage is `tss_test_evidence_confirmation_pending`, the agent must ask explicitly:

- `window_contract` 这一组冻结什么？
- `formal_gate_contract` 这一组冻结什么？
- `admissibility_contract` 这一组冻结什么？
- `audit_contract` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 event forward return、performance summary、test gate table、selected variants？
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
- `是否按以上内容冻结 tss_test_evidence？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `tss_test_evidence`.

When `research_route = time_series_signal` and the stage is `tss_backtest_ready_confirmation_pending`, the agent must ask explicitly:

- `execution_policy` 这一组冻结什么？
- `portfolio_policy` 这一组冻结什么？
- `risk_overlay` 这一组冻结什么？
- `engine_contract` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 strategy contract、engine compare、position timeseries、trade ledger、backtest gate table？
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
- `是否按以上内容冻结 tss_backtest_ready？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `tss_backtest_ready`.

When `research_route = time_series_signal` and the stage is `tss_holdout_validation_confirmation_pending`, the agent must ask explicitly:

- `window_contract` 这一组冻结什么？
- `reuse_contract` 这一组冻结什么？
- `drift_audit` 这一组冻结什么？
- `failure_governance` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 holdout signal diagnostics、event comparison、backtest comparison artifacts？
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
- `是否按以上内容冻结 tss_holdout_validation？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `tss_holdout_validation`.

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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
- `是否确认进入 mandate？`

Do not skip this question. Do not imply the transition already happened.

When the stage is `data_ready_confirmation_pending`, the agent must ask explicitly:

- `extraction_contract` 这一组冻结什么？
- `quality_semantics` 这一组冻结什么？
- `universe_admission` 这一组冻结什么？
- `shared_derived_layer` 这一组冻结什么？
- `delivery_contract` 这一组冻结什么？
- 当前 research repo 里将真实生成哪些 dense data、rolling caches、QC/coverage artifacts？
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
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
- 可一次回显全部 freeze groups；若用户回复 `确认全部`，先批量确认 groups，再继续最终 stage 冻结确认
- `是否按以上内容冻结 csf_holdout_validation？`

Do not skip this question. Do not imply the transition already happened.
Do not accept empty directories, placeholder artifacts, or contract-only docs as completed `csf_holdout_validation`.

## State Source Of Truth

Use disk artifacts as the primary state:

- `outputs/<lineage>/00_idea_intake/`
- `outputs/<lineage>/01_mandate/`
- `outputs/<lineage>/02_tss_data_ready/`
- `outputs/<lineage>/03_tss_signal_ready/`
- `outputs/<lineage>/04_tss_train_freeze/`
- `outputs/<lineage>/05_tss_test_evidence/`
- `outputs/<lineage>/06_tss_backtest_ready/`
- `outputs/<lineage>/07_tss_holdout_validation/`

Legacy unprefixed time_series_signal directories may exist in older fixtures or archived lineages, but they are not canonical for new `time_series_signal` lineages:

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
- tss_data_ready review closure artifacts
- tss_signal_ready review closure artifacts
- tss_train_freeze review closure artifacts
- tss_test_evidence review closure artifacts
- tss_backtest_ready review closure artifacts
- tss_holdout_validation review closure artifacts
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
- Do not bypass tss_data_ready review closure
- Do not bypass tss_signal_ready review closure
- Do not bypass tss_train_freeze transition approval
- Do not bypass tss_train_freeze review closure
- Do not bypass tss_test_evidence transition approval
- Do not bypass tss_test_evidence review closure
- Do not bypass tss_backtest_ready transition approval
- Do not bypass tss_backtest_ready review closure
- Do not bypass tss_holdout_validation transition approval
- Do not bypass tss_holdout_validation review closure
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
- `qros-tss-data-ready-author`
- `qros-tss-data-ready-review`
- `qros-tss-signal-ready-author`
- `qros-tss-signal-ready-review`
- `qros-tss-train-freeze-author`
- `qros-tss-train-freeze-review`
- `qros-tss-test-evidence-author`
- `qros-tss-test-evidence-review`
- `qros-tss-backtest-ready-author`
- `qros-tss-backtest-ready-review`
- `qros-tss-holdout-validation-author`
- `qros-tss-holdout-validation-review`
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
