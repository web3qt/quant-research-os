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
- stop after `mandate review`

## 4. What You Should See

You should see the agent report:

- `lineage`
- `current_stage`
- `artifacts_written`
- `gate_status`
- `next_action`

The underlying runtime will write artifacts under `outputs/<lineage_id>/`.

## 5. Internal Runtime Note

QROS still uses scripts internally for deterministic state transitions, but those are runtime internals, not the primary user workflow.

## 6. Next

After `mandate review`, this version stops. `data_ready` orchestration is not yet part of the single-entry flow.
