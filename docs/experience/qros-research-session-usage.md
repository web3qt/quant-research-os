# QROS Research Session Usage

## What It Is

`qros-research-session` is the single-entry orchestrator for the first QROS workflow slice.

Instead of remembering multiple commands, you start with one skill and let QROS decide where the lineage currently is.

## First-Wave Boundary

This version covers:

- `idea_intake`
- `mandate`
- `mandate review`
- `data_ready`
- `data_ready review`

This version does **not** continue into:

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

For debugging or manual recovery, explicit data_ready approval can also be triggered through:

```bash
python scripts/run_research_session.py --outputs-root outputs --lineage-id <lineage_id> --confirm-data-ready
```

用户不需要记住内部命令。正常路径里，agent 会在对话中停下来确认是否继续进入 mandate 和 data_ready。

## How Stage Detection Works

The session runtime checks disk state in this order:

1. no intake scaffold yet -> `idea_intake`
2. intake exists but not admitted -> `idea_intake`
3. intake admitted but not explicitly approved -> `mandate_confirmation_pending`
4. intake admitted and explicitly approved, but mandate not built -> `mandate`
5. mandate artifacts exist but review closure is missing -> `mandate review`
6. mandate review closure exists -> `data_ready_confirmation_pending`
7. data_ready artifacts exist but review closure is missing -> `data_ready review`
8. data_ready review closure exists -> session stops and reports completion

## Expected User Experience

You start from one skill:

- `qros-research-session`

Then the system:

- resolves or creates the lineage
- scaffolds intake if needed
- reports the current stage
- writes deterministic artifacts when it can
- stops to ask for missing research judgments or explicit governance approval
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

## Example Path

1. Start with a raw idea about BTC leading alt reactions
2. QROS creates a lineage and scaffolds `00_idea_intake/`
3. Intake artifacts are filled and `idea_gate_decision.yaml` is produced
4. If verdict is `GO_TO_MANDATE`, QROS stops at `mandate_confirmation_pending`
5. QROS enters grouped freeze mode instead of silently writing mandate
6. QROS confirms `research_intent`
7. QROS confirms `scope_contract`
8. QROS confirms `data_contract`
   这里会明确问数据来源和 `bar_size`
9. QROS confirms `execution_contract`
10. QROS shows the final grouped mandate summary and asks `是否确认进入 mandate？`
11. The user answers in natural language
12. The agent internally records the approval decision and then builds `01_mandate/`
13. Once mandate review closure exists, QROS enters `data_ready_confirmation_pending`
14. QROS confirms `extraction_contract`
15. QROS confirms `quality_semantics`
16. QROS confirms `universe_admission`
17. QROS confirms `shared_derived_layer`
18. QROS confirms `delivery_contract`
19. QROS shows the final grouped data_ready summary and asks `是否按以上内容冻结 data_ready？`
20. The agent internally records the approval decision and then builds `02_data_ready/`
21. Once data_ready review closure exists, the session stops instead of entering `signal_ready`

## Why This Exists

The goal is to hide internal scripts behind a coherent skill flow.

The scripts still matter as the deterministic runtime, but the user should primarily interact through `qros-research-session`.
