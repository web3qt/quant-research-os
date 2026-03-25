# QROS Research Session Usage

## What It Is

`qros-research-session` is the single-entry orchestrator for the first QROS workflow slice.

Instead of remembering multiple commands, you start with one skill and let QROS decide where the lineage currently is.

## First-Wave Boundary

This version covers:

- `idea_intake`
- `mandate`
- `mandate review`

This version does **not** continue into:

- `data_ready`
- `signal_ready`
- later research stages

## User Entry

In Codex, start with:

- `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
- `qros-research-session help`

The agent should then drive the session for you.

## Internal Runtime

The deterministic backend entry point is still:

```bash
python scripts/run_research_session.py --outputs-root outputs --raw-idea "BTC leads high-liquidity alts after shock events"
```

For debugging or manual recovery, explicit mandate approval can also be triggered through:

```bash
python scripts/run_research_session.py --outputs-root outputs --lineage-id <lineage_id> --confirm-mandate
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate。

## How Stage Detection Works

The session runtime checks disk state in this order:

1. no intake scaffold yet -> `idea_intake`
2. intake exists but not admitted -> `idea_intake`
3. intake admitted but not explicitly approved -> `mandate_confirmation_pending`
4. intake admitted and explicitly approved, but mandate not built -> `mandate`
5. mandate artifacts exist but review closure is missing -> `mandate review`
6. mandate review closure exists -> session stops and reports completion

## Expected User Experience

You start from one skill:

- `qros-research-session`

Then the system:

- resolves or creates the lineage
- scaffolds intake if needed
- reports the current stage
- writes deterministic artifacts when it can
- stops to ask for missing research judgments or explicit governance approval
- asks `是否确认进入 mandate？` before mandate generation

## Example Path

1. Start with a raw idea about BTC leading alt reactions
2. QROS creates a lineage and scaffolds `00_idea_intake/`
3. Intake artifacts are filled and `idea_gate_decision.yaml` is produced
4. If verdict is `GO_TO_MANDATE`, QROS stops at `mandate_confirmation_pending`
5. QROS reports `why_now`, `open_risks`, and asks `是否确认进入 mandate？`
6. The user answers in natural language
7. The agent internally records the approval decision and then builds `01_mandate/`
8. Once mandate review closure exists, the session stops instead of entering `data_ready`

## Why This Exists

The goal is to hide internal scripts behind a coherent skill flow.

The scripts still matter as the deterministic runtime, but the user should primarily interact through `qros-research-session`.
