# QROS Research Session Usage

## What It Is

`qros-research-session` is the single-entry orchestrator for the current QROS workflow slice.

Instead of remembering multiple commands, you start with one skill and let QROS decide where the lineage currently is.

## First-Wave Boundary

This version covers:

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

This version does **not** continue into:

- later research stages

## User Entry

In Codex, start with:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`

The agent should then drive the session for you.

Codex finds the skill through `~/.agents/skills/qros`, which should point to `~/.codex/qros/skills`.

对于一个全新的 raw idea，正常行为不应该是直接替用户完成 `qualification_scorecard.yaml` 和 `idea_gate_decision.yaml`。第一轮应该先停在 `idea_intake_confirmation_pending`，先问清 observation、hypothesis、scope、data source、`bar_size` 和 kill criteria，并在得到显式确认后再进入正式 qualification。

## Internal Runtime

The deterministic backend entry point lives in the cloned repo:

```bash
~/.codex/qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
```

For debugging or manual recovery, explicit intake interview approval can also be triggered through:

```bash
~/.codex/qros/bin/qros-session --lineage-id <lineage_id> --confirm-intake
```

For debugging or manual recovery, explicit mandate approval can also be triggered through:

```bash
~/.codex/qros/bin/qros-session --lineage-id <lineage_id> --confirm-mandate
```

For debugging or manual recovery, explicit data_ready approval can also be triggered through:

```bash
~/.codex/qros/bin/qros-session --lineage-id <lineage_id> --confirm-data-ready
```

For debugging or manual recovery, explicit signal_ready approval can also be triggered through:

```bash
~/.codex/qros/bin/qros-session --lineage-id <lineage_id> --confirm-signal-ready
```

For debugging or manual recovery, explicit train_freeze approval can also be triggered through:

```bash
~/.codex/qros/bin/qros-session --lineage-id <lineage_id> --confirm-train-freeze
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready 和 train_freeze。

For debugging or manual recovery, explicit test_evidence approval can also be triggered through:

```bash
~/.codex/qros/bin/qros-session --lineage-id <lineage_id> --confirm-test-evidence
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready、train_freeze 和 test_evidence。

For debugging or manual recovery, explicit backtest_ready approval can also be triggered through:

```bash
~/.codex/qros/bin/qros-session --lineage-id <lineage_id> --confirm-backtest-ready
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready、train_freeze、test_evidence 和 backtest_ready。

For debugging or manual recovery, explicit holdout_validation approval can also be triggered through:

```bash
~/.codex/qros/bin/qros-session --lineage-id <lineage_id> --confirm-holdout-validation
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate、data_ready、signal_ready、train_freeze、test_evidence、backtest_ready 和 holdout_validation。

## How Stage Detection Works

The session runtime checks disk state in this order:

1. no intake scaffold yet -> `idea_intake`
2. intake scaffold exists but intake interview is not explicitly approved -> `idea_intake_confirmation_pending`
3. intake interview approved but intake gate is not yet admitted -> `idea_intake`
4. intake admitted but not explicitly approved for mandate -> `mandate_confirmation_pending`
5. intake admitted and explicitly approved, but mandate not built -> `mandate`
6. mandate artifacts exist but review closure is missing -> `mandate review`
7. mandate review closure exists -> `data_ready_confirmation_pending`
8. data_ready artifacts exist but review closure is missing -> `data_ready review`
9. data_ready review closure exists -> `signal_ready_confirmation_pending`
10. signal_ready artifacts exist but review closure is missing -> `signal_ready review`
11. signal_ready review closure exists -> `train_freeze_confirmation_pending`
12. train_freeze artifacts exist but review closure is missing -> `train_freeze review`
13. train_freeze review closure exists -> `test_evidence_confirmation_pending`
14. test_evidence artifacts exist but review closure is missing -> `test_evidence review`
15. test_evidence review closure exists -> `backtest_ready_confirmation_pending`
16. backtest_ready artifacts exist but review closure is missing -> `backtest_ready review`
17. backtest_ready review closure exists -> `holdout_validation_confirmation_pending`
18. holdout_validation artifacts exist but review closure is missing -> `holdout_validation review`
19. holdout_validation review closure exists -> session stops and reports completion

## Expected User Experience

You start from one skill:

- `qros-research-session`

Then the system:

- resolves or creates the lineage
- scaffolds intake if needed
- reports the current stage
- writes deterministic artifacts when it can
- stops to ask for missing research judgments or explicit governance approval
- for a brand-new idea, first asks intake questions instead of silently finalizing qualification
- asks one explicit confirmation question before turning the intake interview into a real qualification verdict
- confirms `observation`
- confirms `primary hypothesis`
- confirms `counter-hypothesis`
- confirms `market` / `universe` / `target_task`
- confirms `data_source` / `bar_size`
- confirms `kill criteria` or `reframe` conditions
- freezes mandate interactively by group
- confirms `research_intent`
- confirms `scope_contract`
- confirms `data_contract`
  这里会明确问数据来源哪里来，以及后续研究周期基于什么 `bar_size`，例如 `1m`、`5m`、`15m`
- confirms `execution_contract`
- asks `是否确认进入 mandate？` before mandate generation
- after mandate review closure, freezes data_ready interactively by group
- confirms `extraction_contract`
- confirms `quality_semantics`
- confirms `universe_admission`
- confirms `shared_derived_layer`
- confirms `delivery_contract`
- asks `是否按以上内容冻结 data_ready？` before data_ready generation
- after data_ready review closure, freezes signal_ready interactively by group
- confirms `signal_expression`
- confirms `param_identity`
- confirms `time_semantics`
- confirms `signal_schema`
- confirms `delivery_contract`
- asks `是否按以上内容冻结 signal_ready？` before signal_ready generation
- after signal_ready review closure, freezes train_freeze interactively by group
- confirms `window_contract`
- confirms `threshold_contract`
- confirms `quality_filters`
- confirms `param_governance`
- confirms `delivery_contract`
- asks `是否按以上内容冻结 train_freeze？` before train_freeze generation
- after train_freeze review closure, freezes test_evidence interactively by group
- confirms `window_contract`
- confirms `formal_gate_contract`
- confirms `admissibility_contract`
- confirms `audit_contract`
- confirms `delivery_contract`
- asks `是否按以上内容冻结 test_evidence？` before test_evidence generation
- after test_evidence review closure, freezes backtest_ready interactively by group
- confirms `execution_policy`
- confirms `portfolio_policy`
- confirms `risk_overlay`
- confirms `engine_contract`
- confirms `delivery_contract`
- asks `是否按以上内容冻结 backtest_ready？` before backtest_ready generation
- after backtest_ready review closure, freezes holdout_validation interactively by group
- confirms `window_contract`
- confirms `reuse_contract`
- confirms `drift_audit`
- confirms `failure_governance`
- confirms `delivery_contract`
- asks `是否按以上内容冻结 holdout_validation？` before holdout_validation generation

## Example Path

1. Start with a raw idea about BTC leading alt reactions
2. QROS creates a lineage and scaffolds `00_idea_intake/`
3. QROS first asks intake questions instead of silently finalizing qualification
4. Intake artifacts are then filled and `idea_gate_decision.yaml` is produced
5. If verdict is `GO_TO_MANDATE`, QROS stops at `mandate_confirmation_pending`
6. QROS enters grouped freeze mode instead of silently writing mandate
7. QROS confirms `research_intent`
8. QROS confirms `scope_contract`
9. QROS confirms `data_contract`
   这里会明确问数据来源和 `bar_size`
10. QROS confirms `execution_contract`
11. QROS shows the final grouped mandate summary and asks `是否确认进入 mandate？`
12. The user answers in natural language
13. The agent internally records the approval decision and then builds `01_mandate/`
14. Once mandate review closure exists, QROS enters `data_ready_confirmation_pending`
14. QROS confirms `extraction_contract`
15. QROS confirms `quality_semantics`
16. QROS confirms `universe_admission`
17. QROS confirms `shared_derived_layer`
18. QROS confirms `delivery_contract`
19. QROS shows the final grouped data_ready summary and asks `是否按以上内容冻结 data_ready？`
20. The agent internally records the approval decision and then builds `02_data_ready/`
21. Once data_ready review closure exists, QROS enters `signal_ready_confirmation_pending`
22. QROS confirms `signal_expression`
23. QROS confirms `param_identity`
24. QROS confirms `time_semantics`
25. QROS confirms `signal_schema`
26. QROS confirms `delivery_contract`
27. QROS shows the final grouped signal_ready summary and asks `是否按以上内容冻结 signal_ready？`
28. The agent internally records the approval decision and then builds `03_signal_ready/`
29. Once signal_ready review closure exists, QROS enters `train_freeze_confirmation_pending`
30. QROS confirms `window_contract`
31. QROS confirms `threshold_contract`
32. QROS confirms `quality_filters`
33. QROS confirms `param_governance`
34. QROS confirms `delivery_contract`
35. QROS shows the final grouped train_freeze summary and asks `是否按以上内容冻结 train_freeze？`
36. The agent internally records the approval decision and then builds `04_train_freeze/`
37. Once train_freeze review closure exists, QROS enters `test_evidence_confirmation_pending`
38. QROS confirms `window_contract`
39. QROS confirms `formal_gate_contract`
40. QROS confirms `admissibility_contract`
41. QROS confirms `audit_contract`
42. QROS confirms `delivery_contract`
43. QROS shows the final grouped test_evidence summary and asks `是否按以上内容冻结 test_evidence？`
44. The agent internally records the approval decision and then builds `05_test_evidence/`
45. Once test_evidence review closure exists, QROS enters `backtest_ready_confirmation_pending`
46. QROS confirms `execution_policy`
47. QROS confirms `portfolio_policy`
48. QROS confirms `risk_overlay`
49. QROS confirms `engine_contract`
50. QROS confirms `delivery_contract`
51. QROS shows the final grouped backtest_ready summary and asks `是否按以上内容冻结 backtest_ready？`
52. The agent internally records the approval decision and then builds `06_backtest/`
53. Once backtest_ready review closure exists, QROS enters `holdout_validation_confirmation_pending`
54. QROS confirms `window_contract`
55. QROS confirms `reuse_contract`
56. QROS confirms `drift_audit`
57. QROS confirms `failure_governance`
58. QROS confirms `delivery_contract`
59. QROS shows the final grouped holdout_validation summary and asks `是否按以上内容冻结 holdout_validation？`
60. The agent internally records the approval decision and then builds `07_holdout/`
61. Once holdout_validation review closure exists, the session stops instead of entering later stages

## Why This Exists

The goal is to hide internal scripts behind a coherent skill flow.

The scripts still matter as the deterministic runtime, but the user should primarily interact through `qros-research-session`.
