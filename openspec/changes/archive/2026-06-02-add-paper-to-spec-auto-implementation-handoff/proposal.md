## Why

`qros-paper-to-spec` currently stops after producing staged PaperSpec artifacts, even when those specs are valid and actionable. Researchers need an explicit post-spec handoff that asks whether to implement from the generated specs, and the data layer must first surface required datasets before any implementation or data acquisition begins.

## What Changes

- Add a post-spec implementation handoff prompt after all requested PaperSpec artifacts are generated and validated.
- Require the handoff to ask the researcher whether QROS should automatically implement from the specs in the active research repo.
- Add a data readiness brief before implementation that lists required and optional datasets, expected fields, market scope, time range, cadence, source constraints, and missing-data policy.
- Require the agent to ask whether the researcher can provide the required data before attempting acquisition.
- Allow agent-driven data acquisition only after researcher confirmation that data cannot be provided, and only with explicit source, command, snapshot, provenance, and failure records.
- Preserve the QROS framework repo boundary: implementation code, downloaded data, snapshots, and live lineage artifacts must belong to the active research repo, not this governance repo.

## Capabilities

### New Capabilities

- `paper-to-spec-implementation-handoff`: Defines the post-PaperSpec implementation prompt, data readiness brief, researcher data handoff, and controlled agent data acquisition behavior.

### Modified Capabilities

- None.

## Impact

- Affects `skills/core/qros-paper-to-spec/SKILL.md` and its user-facing docs.
- May add or update contracts under `contracts/paper_to_spec/` if the data readiness brief becomes a machine-readable artifact.
- May add runtime helpers and tests if the implementation handoff is generated or validated deterministically.
- Does not change `qros-research-session` stage flow, review orchestration, route split, or failure handling.
- Does not allow implementation artifacts or acquired data to be written into the QROS framework repo.
