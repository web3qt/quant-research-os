# QROS Stage Display Skill Usage

## Purpose

`qros-stage-display` now uses a two-layer contract:

- runtime writes a deterministic structured summary plus native-subagent handoff artifacts
- any Codex session can consume that handoff and visibly spawn a subagent to render the HTML page

## v1 Supported Stages

- `mandate`
- `data_ready`
- `signal_ready`
- `train_freeze`
- `test_evidence`
- `backtest_ready`
- `holdout_validation`
- `csf_data_ready`
- `csf_signal_ready`
- `csf_train_freeze`
- `csf_test_evidence`
- `csf_backtest_ready`
- `csf_holdout_validation`

The runtime is intentionally registry-thin:

- one generic skill surface
- `mandate` and `csf_data_ready` keep stage-specific summary builders
- the remaining reviewable mainline / CSF stages use the shared generic review-closure builder
- explicit fail-fast behavior for any unsupported stage

## Output Location

Runtime first writes:

- `<lineage_root>/reports/stage_display/<stage>.summary.json`
- `<lineage_root>/reports/stage_display/<stage>.display_request.json`
- `<lineage_root>/reports/stage_display/<stage>.display_prompt.txt`

After a Codex-native visible subagent completes rendering, it writes back:

- `<lineage_root>/reports/stage_display/<stage>.summary.html`
- `<lineage_root>/reports/stage_display/<stage>.display_result.json`

`qros-research-session` reads the result artifact to decide whether display is still pending, failed, or complete.

## Command

Generate deterministic summary + handoff artifact:

```bash
python scripts/run_stage_display.py \
  --stage-id mandate \
  --lineage-root <lineage-root> \
  --json
```

Or:

```bash
python scripts/run_stage_display.py \
  --stage-id csf_data_ready \
  --outputs-root <outputs-root> \
  --lineage-id <lineage-id> \
  --json
```

## Structured Summary Contract

The summary JSON includes at least:

- `stage_id`
- `lineage_id`
- `lineage_root`
- `stage_directory`
- `section_order`
- `sections[]`
- explicit item markers: `available`, `missing`, `question`

`mandate` still reflects only frozen mandate artifacts plus explicit review closure artifacts, for example:

- research question / route / factor identity
- scope and data contract facts already frozen into mandate outputs
- execution and review closure evidence

`csf_data_ready` still reflects only frozen artifact and contract facts such as:

- panel manifest evidence
- universe / eligibility / coverage evidence
- run manifest / rebuild / delivery evidence

Other supported reviewable stages use a generic deterministic summary shape that stays bounded to:

- stage metadata and core review evidence
- frozen artifact inventory
- review closure artifacts

No supported stage display path parses parquet internals or makes performance claims.

## Completing the render from another Codex session

In another Codex session, read:

- `*.display_request.json`
- `*.display_prompt.txt`

Then spawn a native visible subagent to render HTML to the requested `html_output_path`.
After that HTML exists, write the completion artifact with:

```bash
python scripts/run_stage_display.py \
  --stage-id mandate \
  --lineage-root <lineage-root> \
  --complete-from-html <rendered-html-path> \
  --json
```

## Testing / Controlled Renderers

For tests or controlled wrappers, you may override the render command:

```bash
python scripts/run_stage_display.py \
  --stage-id mandate \
  --lineage-root <lineage-root> \
  --renderer-command "python path/to/render_stub.py" \
  --json
```

This compatibility path is for tests / controlled wrappers. It is **not** the canonical native-subagent display path.
