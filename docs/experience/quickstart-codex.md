# QROS Quickstart For Codex

## 1. Install

Choose one:

```bash
./setup --host codex --mode user-global
```

or

```bash
./setup --host codex --mode repo-local
```

## 2. Start From The Unified Skill

In Codex, start with:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`

## 3. Let The Agent Drive The First-Wave Flow

This version of QROS will drive:

- `idea_intake`
- `mandate`
- `mandate review`

The agent should:

- create or resume the lineage
- scaffold intake artifacts when needed
- ask only for missing research judgments
- stop at `mandate_confirmation_pending` when intake is admitted
- confirm grouped freeze content during the conversation: `research_intent`, `scope_contract`, `data_contract`, `execution_contract`
- explicitly ask `是否确认进入 mandate？` before writing `01_mandate/`
- stop after `mandate review`

## 4. What You Should See

You should see the agent report:

- `lineage`
- `current_stage`
- `artifacts_written`
- `gate_status`
- `next_action`
- `why_now`
- `open_risks`

The underlying runtime will write artifacts under `outputs/<lineage_id>/`.

## 5. Internal Runtime Note

QROS still uses scripts internally for deterministic state transitions, but those are runtime internals, not the primary user workflow.

## 6. Next

After `mandate review`, this version stops. `data_ready` orchestration is not yet part of the single-entry flow.
