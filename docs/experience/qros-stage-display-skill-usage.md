# QROS Stage Display Skill Usage

## Purpose

`qros-stage-display` turns a frozen stage directory into two artifacts:

- a deterministic structured summary JSON
- a Codex-subagent-rendered HTML summary page

This is the supported skill-native path for stage display work. It replaces the older pattern of exporting a handoff bundle and rendering HTML manually outside the skill boundary.

## v1 Supported Stages

- `csf_data_ready`

The runtime is intentionally registry-thin:

- one generic skill surface
- one registered stage builder in v1
- explicit fail-fast behavior for any unsupported stage

## Output Location

Successful runs write to:

- `<lineage_root>/reports/stage_display/csf_data_ready.summary.json`
- `<lineage_root>/reports/stage_display/csf_data_ready.summary.html`

If the subagent render step fails, the run fails and only the summary JSON may remain as an `incomplete_diagnostic` artifact.

## Command

```bash
python scripts/run_stage_display.py \
  --stage-id csf_data_ready \
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

`csf_data_ready` v1 reflects only frozen artifact and contract facts such as:

- panel manifest evidence
- universe / eligibility / coverage evidence
- run manifest / rebuild / delivery evidence

It does **not** parse parquet internals or make performance claims.

## Testing / Controlled Renderers

For tests or controlled wrappers, you may override the render command:

```bash
python scripts/run_stage_display.py \
  --stage-id csf_data_ready \
  --lineage-root <lineage-root> \
  --renderer-command "python path/to/render_stub.py" \
  --json
```

The default path uses `codex exec` as the required render worker.
