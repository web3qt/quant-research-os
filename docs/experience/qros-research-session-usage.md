# QROS Research Session Usage

## What It Is

`qros-research-session` is the single-entry orchestrator for the first QROS workflow slice.

Instead of remembering multiple commands, you start with one session and let QROS decide where the lineage currently is.

## First-Wave Boundary

This version covers:

- `idea_intake`
- `mandate`
- `mandate review`

This version does **not** continue into:

- `data_ready`
- `signal_ready`
- later research stages

## Runtime Entry

The deterministic backend entry point is:

```bash
python scripts/run_research_session.py --outputs-root outputs --raw-idea "BTC leads high-liquidity alts after shock events"
```

To resume an existing lineage:

```bash
python scripts/run_research_session.py --outputs-root outputs --lineage-id btc_leads_high_liquidity_alts_after_shock_events
```

## How Stage Detection Works

The session runtime checks disk state in this order:

1. no intake scaffold yet -> `idea_intake`
2. intake exists but not admitted -> `idea_intake`
3. intake admitted but mandate not built -> `mandate`
4. mandate artifacts exist but review closure is missing -> `mandate review`
5. mandate review closure exists -> session stops and reports completion

## Expected User Experience

You start from one skill:

- `qros-research-session`

Then the system:

- resolves or creates the lineage
- scaffolds intake if needed
- reports the current stage
- writes deterministic artifacts when it can
- stops to ask only for missing research judgments

## Example Path

1. Start with a raw idea about BTC leading alt reactions
2. QROS creates a lineage and scaffolds `00_idea_intake/`
3. Intake artifacts are filled and `idea_gate_decision.yaml` is produced
4. If verdict is `GO_TO_MANDATE`, QROS builds `01_mandate/`
5. QROS reports that the next state is `mandate review`
6. Once mandate review closure exists, the session stops instead of entering `data_ready`

## Why This Exists

The goal is to hide internal scripts behind a coherent skill flow.

The scripts still matter as the deterministic runtime, but the user should primarily interact through `qros-research-session`.
