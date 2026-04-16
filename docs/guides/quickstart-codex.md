# QROS Quickstart For Codex

## 1. Install

If you want the shortest Codex-native path, tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

Or install manually:

```bash
git clone <QROS_REPO_URL> ~/workspace/quant-research-os
cd ~/workspace/quant-research-os
./setup --host codex --mode user-global
```

Then, from the current research repo root:

```bash
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

## 2. Start From The Unified Skill

In Codex, start with:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`
- `qros-update`

正常用户从这里开始，不需要先跑 `./.qros/bin/qros-session`。

如果你第一次看到 `research_intent`、`window_contract`、`delivery_contract` 这类 group 名，先看：

- `docs/guides/stage-freeze-group-field-guide.md`

## 3. Let The Agent Drive The Current Flow

This version of QROS will drive:

- `idea_intake`
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

The agent should:

- create or resume the lineage
- scaffold intake artifacts when needed
- ask only for missing research judgments
- stop at `idea_intake_confirmation_pending` for a brand-new raw idea
- explicitly confirm the intake interview before treating qualification as final
- stop at `mandate_confirmation_pending` when intake is admitted
- confirm grouped freeze content during the conversation: `research_intent`, `scope_contract`, `data_contract`, `execution_contract`
- explicitly ask `是否确认进入 mandate？` before writing `01_mandate/`
- continue into `data_ready_confirmation_pending` after mandate review closure
- confirm grouped data_ready content during the conversation: `extraction_contract`, `quality_semantics`, `universe_admission`, `shared_derived_layer`, `delivery_contract`
- make the active research repo materially generate the shared data outputs and QC or coverage evidence promised by that freeze
- never treat empty directories, placeholder files, or contract-only markdown as completed `data_ready`
- explicitly ask `是否按以上内容冻结 data_ready？` before writing `02_data_ready/`
- continue into `signal_ready_confirmation_pending` after data_ready review closure
- confirm grouped signal_ready content during the conversation: `signal_expression`, `param_identity`, `time_semantics`, `signal_schema`, `delivery_contract`
- make the active research repo materially generate baseline signal timeseries, param manifests and coverage evidence promised by that freeze
- never treat empty directories, placeholder files, or contract-only markdown as completed `signal_ready`
- explicitly ask `是否按以上内容冻结 signal_ready？` before writing `03_signal_ready/`
- continue into `train_freeze_confirmation_pending` after signal_ready review closure
- confirm grouped train_freeze content during the conversation: `window_contract`, `threshold_contract`, `quality_filters`, `param_governance`, `delivery_contract`
- make the active research repo materially generate train thresholds, quality outputs and ledgers promised by that freeze
- never treat empty directories, placeholder files, or contract-only markdown as completed `train_freeze`
- explicitly ask `是否按以上内容冻结 train_freeze？` before writing `04_train_freeze/`
- continue into `test_evidence_confirmation_pending` after train_freeze review closure
- confirm grouped test_evidence content during the conversation: `window_contract`, `formal_gate_contract`, `admissibility_contract`, `audit_contract`, `delivery_contract`
- make the active research repo materially generate test statistics, admissibility outputs and frozen selections promised by that freeze
- never treat empty directories, placeholder files, or contract-only markdown as completed `test_evidence`
- explicitly ask `是否按以上内容冻结 test_evidence？` before writing `05_test_evidence/`
- continue into `backtest_ready_confirmation_pending` after test_evidence review closure
- confirm grouped backtest_ready content during the conversation: `execution_policy`, `portfolio_policy`, `risk_overlay`, `engine_contract`, `delivery_contract`
- make the active research repo materially generate dual-engine backtest outputs, combo ledgers and capacity evidence promised by that freeze
- never treat empty directories, placeholder files, or contract-only markdown as completed `backtest_ready`
- explicitly ask `是否按以上内容冻结 backtest_ready？` before writing `06_backtest/`
- continue into `holdout_validation_confirmation_pending` after backtest_ready review closure
- confirm grouped holdout_validation content during the conversation: `window_contract`, `reuse_contract`, `drift_audit`, `failure_governance`, `delivery_contract`
- make the active research repo materially generate single-window, merged-window and comparison outputs promised by that freeze
- never treat empty directories, placeholder files, or contract-only markdown as completed `holdout_validation`
- explicitly ask `是否按以上内容冻结 holdout_validation？` before writing `07_holdout/`
- stop after `holdout_validation review`

## 4. What You Should See

You should see the agent report:

- `lineage`
- `current_stage`
- `artifacts_written`
- `gate_status`
- `next_action`
- `why_now`
- `open_risks`

The underlying runtime will write artifacts under `outputs/<lineage_id>/` in the active research repo.

For `data_ready` and later stages, those artifacts are expected to be real stage deliverables. Directory skeletons, placeholder files, and doc-only stand-ins are not enough to claim the stage is complete.

Review failure is not ordinary debugging. If a stage review ends with `PASS FOR RETRY`, `RETRY`, `NO-GO`, or `CHILD LINEAGE`, the session should stop normal stage progression, surface `requires_failure_handling`, and switch into `qros-stage-failure-handler`.

## 5. Internal Runtime Note

QROS still uses scripts internally for deterministic state transitions, but those are runtime internals, not the primary user workflow.

## 6. Next

After `holdout_validation review`, this version stops. That is the current terminal stage of the single-entry flow.

Codex discovers QROS directly through `~/.codex/skills/`; `./setup` writes the flat installed `qros-*` skills there.
