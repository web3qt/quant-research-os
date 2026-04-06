---
name: qros-stage-display
description: Use when a frozen stage needs a stage-display summary skill that produces a structured summary plus subagent-rendered HTML.
---

# QROS Stage Display

## Purpose

把已冻结阶段的关键交付物整理成一个正式的 display surface，而不是一次性脚本或手工 bundle。

这个 skill 是 **generic by shape, registry-thin by implementation**：

- 只有一个统一 skill 入口
- 具体阶段语义仍由 repo-owned stage builder 决定
- v1 **只正式支持** `csf_data_ready`

## v1 Supported Stage List

- `csf_data_ready`

v1 formally supports **only** `csf_data_ready`.

No other stage is supported in v1.

任何未注册阶段都必须显式失败：

- `Unsupported stage for qros-stage-display: <stage_id>`
- 不得写出 partial HTML
- 不得假装 fallback 到其他 stage

## Required Inputs For `csf_data_ready`

- `02_csf_data_ready/panel_manifest.json`
- `02_csf_data_ready/asset_universe_membership.parquet`
- `02_csf_data_ready/eligibility_base_mask.parquet`
- `02_csf_data_ready/cross_section_coverage.parquet`
- `02_csf_data_ready/shared_feature_base/`
- `02_csf_data_ready/csf_data_contract.md`
- `02_csf_data_ready/run_manifest.json`
- `02_csf_data_ready/artifact_catalog.md`
- `02_csf_data_ready/field_dictionary.md`
- `02_csf_data_ready/rebuild_csf_data_ready.py`

## Required Outputs

Successful runs must write both artifacts under a stable display path:

- `reports/stage_display/csf_data_ready.summary.json`
- `reports/stage_display/csf_data_ready.summary.html`

The JSON summary is the deterministic source of truth.
The HTML artifact is valid only when the required Codex subagent render step succeeds.

## Subagent Contract (Required)

Codex subagent is a **required core worker** in this workflow.

That means:

- the skill must build a deterministic structured summary first
- the skill must then invoke a Codex subagent to render the HTML page
- success requires **both** the structured summary and the rendered HTML
- if subagent rendering fails, the overall run fails
- on render failure, the structured summary may remain only as an explicit incomplete diagnostic artifact

## Fact Boundary

Display content must stay bounded by frozen stage artifacts and contracts.

Forbidden behaviors:

- infer factor performance
- infer alpha quality
- invent coverage explanations not present in the frozen artifacts
- blur `available` / `missing` / `question` markers for presentation polish

## Invocation

From the repo root or installed runtime:

```bash
python scripts/run_stage_display.py \
  --stage-id csf_data_ready \
  --lineage-root <path-to-lineage-root> \
  --json
```

Alternative path resolution:

```bash
python scripts/run_stage_display.py \
  --stage-id csf_data_ready \
  --outputs-root <outputs-root> \
  --lineage-id <lineage-id> \
  --json
```

## Notes

- This skill is generic by entrypoint, not by free-form subagent discovery.
- Add future stages only by registering a new builder plus stage-specific tests.
- Do not widen support by editing the subagent prompt alone.
