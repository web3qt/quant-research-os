# Phase 03 Research: Research Session Entry Discipline

**Phase:** 03 -- Research Session Entry Discipline
**Date:** 2026-05-07
**Status:** Ready for execution

## Scope

Phase 3 hardens the boundary between the normal `qros-research-session` progression path and stage-specific author/review skills.

The current runtime already computes lineage state through `runtime.tools.research_session.detect_session_stage()` and exposes read-only user progress through `qros-progress`. The missing piece is a deterministic admission check that a stage-specific skill can run before it authors or reviews a stage.

## Relevant Existing Mechanisms

- `runtime/tools/research_session.py`
  - Owns canonical `SessionStage` values.
  - Owns `STAGE_ACTIVE_SKILLS`, which maps each runtime state to the skill that is currently allowed to act.
  - Owns `detect_session_stage(lineage_root)`.
- `runtime/tools/progress_runtime.py`
  - Selects the latest lineage or explicit lineage and renders read-only status.
- `runtime/bin/*`
  - Stable installed entrypoints derive `outputs/` from the active research repo root.
- Stage-specific skills under `skills/*/qros-*-author` and `skills/*/qros-*-review`
  - Already describe stage-local contracts, but do not require a runtime state guard before work begins.

## Design Choice

Add a small runtime guard:

```text
qros-check-stage-entry --stage <stage_id> --lane author|review [--lineage-id <id>]
```

The guard should:

- Select the lineage exactly like `qros-progress` when no explicit lineage is passed.
- Read `current_stage` from disk without mutating the research repo.
- Allow author skills only at `<stage>_confirmation_pending` or `<stage>_author` (with the intake special case).
- Allow review skills only at `<stage>_review_confirmation_pending` or `<stage>_review`.
- Reject mismatches with a message containing observed stage, requested stage/lane, expected stages, current active skill, and the recovery command through `qros-research-session`.

## Files To Change

- Add `runtime/tools/stage_entry_guard.py`.
- Add `runtime/scripts/check_stage_entry.py`.
- Add `runtime/bin/qros-check-stage-entry`.
- Update install/bootstrap tests so the new wrapper is installed.
- Update stage author/review skills with a mandatory first-step guard.
- Update docs explaining that `qros-research-session` remains the normal progression gate.

## Validation Strategy

Focused tests:

- Runtime unit tests for allow/block behavior and exact diagnostic fields.
- CLI tests for successful author/review admission and mismatch failure.
- Skill text tests that require `qros-check-stage-entry` as the first stage-specific discipline.
- Bootstrap/install tests that require the wrapper asset.

Because this touches stage flow and installed runtime entrypoints, run `smoke` and `full-smoke`.
