# QROS Agent 行为评估

本文说明 QROS 的真实 agent 行为回归测试边界。

这套 eval 用来验证 agent 是否按 skill-first 方式进入 QROS 工作流，而不是只验证 runtime 函数本身。它关注稳定行为信号：

- 目标 skill 是否触发
- 目标 skill 之前是否出现非白名单 tool call
- runtime status 是否停在预期 stage
- 必要 artifact 是否存在
- 禁止提前生成的 artifact 是否不存在
- `qros-validate-stage` 对 `mandate_admission` / `mandate` shape 是否通过
- `expected_events` 中声明的 validator / preflight / review 命令顺序是否出现

## 执行边界

真实 agent eval 是 manual / nightly，不进入默认 pytest，也不进入 smoke。默认 pytest 只跑 fake transcript、case contract、parser 和 assertion 测试。

原因是模型输出和工具事件格式可能波动。普通 CI 应该验证 harness 本身是稳定的，真实 agent 运行结果作为人工或夜间信号记录。

## 命令

手动运行时使用：

```bash
qros-agent-eval \
  --case naive_raw_idea_triggers_research_session \
  --work-root /tmp/qros-agent-eval \
  --agent-command-template '<agent command that writes JSONL to {transcript_path}>'
```

`--agent-command-template` 是必填项。命令模板可使用这些占位符：

- `{prompt_path}`
- `{transcript_path}`
- `{work_dir}`
- `{prompt}`

每次运行会写出：

- `prompt.txt`
- `transcript.jsonl`
- `result.yaml`

Codex CLI 的 `--json` transcript 里，skill 使用可能不会表现为独立 `Skill` tool event。当前 harness 也会把第一时间读取对应 `.../skills/<skill>/SKILL.md` 的 `command_execution` 归一化为 `skill_call`；其他 `command_execution` 仍按普通 tool call 处理。

## Fake Transcript / 假 Transcript

开发 harness 时不要调用真实模型。使用 fake transcript：

```bash
python runtime/scripts/run_agent_behavior_eval.py \
  --case naive_raw_idea_triggers_research_session \
  --work-root /tmp/qros-agent-eval \
  --transcript-path tests/agent_eval/fixtures/fake_agent_success.jsonl
```

## MVP 用例

- `naive_raw_idea_triggers_research_session`
- `raw_idea_starts_mandate_admission`
- `partial_admission_does_not_freeze_mandate`
- `no_confirmation_no_mandate_formal_artifacts`
- `raw_idea_scaffold_passes_artifact_shape_validator`

## CSF Data Ready 用例

- `explicit_csf_data_ready_author_skill_first`
- `csf_data_ready_rejects_non_csf_mandate`
- `csf_data_ready_rejects_unreviewed_mandate`
- `csf_data_ready_rejects_unconfirmed_freeze_groups`
- `csf_data_ready_rejects_placeholder_parquet_completion`
- `csf_data_ready_runs_validator_before_review`

`csf_data_ready_runs_validator_before_review` 使用 `expected_events.ordered_substrings` 锁定：

```text
qros-validate-stage --stage csf_data_ready
qros-review-preflight
qros-review-cycle prepare
```

这保证 agent 不能跳过 `qros-validate-stage --stage csf_data_ready` 或 preflight 直接进入 reviewer lane。

## CSF Signal Ready 用例

- `explicit_csf_signal_ready_author_skill_first`
- `naive_csf_signal_ready_prompt_triggers_author_skill`
- `csf_signal_ready_rejects_missing_csf_data_ready_review_closure`
- `csf_signal_ready_rejects_non_csf_mandate_route`
- `csf_signal_ready_rejects_unconfirmed_freeze_groups`
- `csf_signal_ready_rejects_placeholder_factor_panel_completion`
- `csf_signal_ready_runs_artifact_validator_before_review`
- `csf_signal_ready_runs_semantic_validator_before_review`
- `csf_signal_ready_rejects_route_inheritance_drift`
- `csf_signal_ready_rejects_raw_field_without_input_binding`

`csf_signal_ready_runs_artifact_validator_before_review` 与
`csf_signal_ready_runs_semantic_validator_before_review` 使用 `expected_events.ordered_substrings` 锁定：

```text
qros-validate-stage --stage csf_signal_ready
csf_signal_ready semantic validator
qros-review-preflight
qros-review-cycle prepare
```

这保证 agent 不能跳过 `qros-validate-stage --stage csf_signal_ready`、semantic validator 或 preflight 直接进入 reviewer lane。

## CSF Train Freeze 用例

- `explicit_csf_train_freeze_author_skill_first`
- `naive_csf_train_freeze_prompt_triggers_author_skill`
- `csf_train_freeze_rejects_missing_csf_signal_ready_review_closure`
- `csf_train_freeze_rejects_unconfirmed_freeze_groups`
- `csf_train_freeze_rejects_placeholder_variant_ledger_completion`
- `csf_train_freeze_runs_artifact_validator_before_review`
- `csf_train_freeze_runs_semantic_validator_before_review`
- `csf_train_freeze_rejects_signal_axis_drift`

`csf_train_freeze_runs_artifact_validator_before_review` 与
`csf_train_freeze_runs_semantic_validator_before_review` 使用 `expected_events.ordered_substrings` 锁定：

```text
qros-validate-stage --stage csf_train_freeze
csf_train_freeze semantic validator
qros-review-preflight
qros-review-cycle prepare
```

这保证 agent 不能跳过 `qros-validate-stage --stage csf_train_freeze`、semantic validator 或 preflight 直接进入 reviewer lane。

## CSF Test Evidence 用例

- `explicit_csf_test_evidence_author_skill_first`
- `naive_csf_test_evidence_prompt_triggers_author_skill`
- `csf_test_evidence_rejects_missing_csf_train_freeze_review_closure`
- `csf_test_evidence_rejects_unconfirmed_freeze_groups`
- `csf_test_evidence_rejects_placeholder_rank_ic_completion`
- `csf_test_evidence_runs_artifact_validator_before_review`
- `csf_test_evidence_runs_semantic_validator_before_review`
- `csf_test_evidence_rejects_variant_drift`

`csf_test_evidence_runs_artifact_validator_before_review` 与
`csf_test_evidence_runs_semantic_validator_before_review` 使用 `expected_events.ordered_substrings` 锁定：

```text
qros-validate-stage --stage csf_test_evidence
csf_test_evidence semantic validator
qros-review-preflight
qros-review-cycle prepare
```

这保证 agent 不能跳过 `qros-validate-stage --stage csf_test_evidence`、semantic validator 或 preflight 直接进入 reviewer lane。

## CSF Backtest Ready 用例

- `explicit_csf_backtest_ready_author_skill_first`
- `naive_csf_backtest_ready_prompt_triggers_author_skill`
- `csf_backtest_ready_rejects_missing_csf_test_evidence_review_closure`
- `csf_backtest_ready_rejects_unconfirmed_freeze_groups`
- `csf_backtest_ready_rejects_placeholder_weight_panel_completion`
- `csf_backtest_ready_runs_artifact_validator_before_review`
- `csf_backtest_ready_runs_semantic_validator_before_review`
- `csf_backtest_ready_rejects_variant_drift`

`csf_backtest_ready_runs_artifact_validator_before_review` 与
`csf_backtest_ready_runs_semantic_validator_before_review` 使用 `expected_events.ordered_substrings` 锁定：

```text
qros-validate-stage --stage csf_backtest_ready
csf_backtest_ready semantic validator
qros-review-preflight
qros-review-cycle prepare
```

这保证 agent 不能跳过 `qros-validate-stage --stage csf_backtest_ready`、semantic validator 或 preflight 直接进入 reviewer lane。

## CSF Holdout Validation 用例

- `explicit_csf_holdout_validation_author_skill_first`
- `naive_csf_holdout_validation_prompt_triggers_author_skill`
- `csf_holdout_validation_rejects_missing_csf_backtest_ready_review_closure`
- `csf_holdout_validation_rejects_unconfirmed_freeze_groups`
- `csf_holdout_validation_rejects_placeholder_compare_completion`
- `csf_holdout_validation_runs_artifact_validator_before_review`
- `csf_holdout_validation_runs_semantic_validator_before_review`
- `csf_holdout_validation_rejects_direction_flip`

`csf_holdout_validation_runs_artifact_validator_before_review` 与
`csf_holdout_validation_runs_semantic_validator_before_review` 使用 `expected_events.ordered_substrings` 锁定：

```text
qros-validate-stage --stage csf_holdout_validation
csf_holdout_validation semantic validator
qros-review-preflight
qros-review-cycle prepare
```

这保证 agent 不能跳过 `qros-validate-stage --stage csf_holdout_validation`、semantic validator 或 preflight 直接进入 reviewer lane。

## TSS 用例

TSS (`time_series_signal`) 的行为 case 对齐 CSF 的 validator-before-review 纪律，但 stage 名和语义使用 `tss_*` 主线：

- `tss_data_ready_runs_validators_before_review`
- `tss_data_ready_rejects_gate`
- `tss_signal_ready_runs_validators_before_review`
- `tss_signal_ready_rejects_gate`
- `tss_train_freeze_runs_validators_before_review`
- `tss_train_freeze_rejects_gate`
- `tss_test_evidence_runs_validators_before_review`
- `tss_test_evidence_rejects_gate`
- `tss_backtest_ready_runs_validators_before_review`
- `tss_backtest_ready_rejects_gate`
- `tss_holdout_validation_runs_validators_before_review`
- `tss_holdout_validation_rejects_gate`

每个 `*_runs_validators_before_review` case 使用 `expected_events.ordered_substrings` 锁定对应阶段的顺序：

```text
qros-validate-stage --stage tss_data_ready
tss_data_ready semantic validator
qros-review-preflight
qros-review-cycle prepare

qros-validate-stage --stage tss_signal_ready
tss_signal_ready semantic validator
qros-review-preflight
qros-review-cycle prepare

qros-validate-stage --stage tss_train_freeze
tss_train_freeze semantic validator
qros-review-preflight
qros-review-cycle prepare

qros-validate-stage --stage tss_test_evidence
tss_test_evidence semantic validator
qros-review-preflight
qros-review-cycle prepare

qros-validate-stage --stage tss_backtest_ready
tss_backtest_ready semantic validator
qros-review-preflight
qros-review-cycle prepare

qros-validate-stage --stage tss_holdout_validation
tss_holdout_validation semantic validator
qros-review-preflight
qros-review-cycle prepare
```

每个 `*_rejects_gate` case 则锁定 gate 被拒后不得继续 reviewer lane：不得出现 `qros-review-cycle prepare`，也不得调用对应 stage review skill。

这些 case 定义在：

```text
contracts/agent_eval/qros_agent_behavior_eval_cases.yaml
```

## 断言原则

不要断言 assistant 的自然语言原文。只断言可稳定复现的行为信号，例如 skill call、tool call 顺序、runtime current_stage、artifact 存在性和 validator 结果。
