---
phase: 02-canonical-csf-stage-identity
plan: 02-01
subsystem: runtime
tags: [qros-runtime, csf, stage-program, review-preflight]
requires: []
provides:
  - canonical CSF stage ids in session and scaffold specs
  - CSF canonical-id to lineage-local program path compatibility
  - focused regression coverage for CSF identity drift
affects: [qros-research-session, stage-program-runtime, review-preflight]
tech-stack:
  added: []
  patterns:
    - canonical route-specific stage ids with local program directory aliases
key-files:
  created: []
  modified:
    - runtime/tools/research_session.py
    - runtime/tools/stage_program_scaffold.py
    - runtime/tools/lineage_program_runtime.py
    - tests/runtime/test_lineage_program_runtime.py
    - tests/session/test_review_entry_preflight_scope.py
    - tests/runtime/test_stage_program_identity.py
    - tests/runtime/test_csf_data_ready_auto_program.py
    - docs/guides/qros-research-session-usage.md
key-decisions:
  - "CSF stage identity is canonical as csf_* in session specs, scaffold manifests, provenance, and review/preflight scope."
  - "Lineage-local CSF program directories remain non-prefixed under program/cross_sectional_factor/<base> for active research repo compatibility."
patterns-established:
  - "stage_program_relative_dir() maps canonical CSF ids to local CSF program directory names."
requirements-completed:
  - CSF-01
  - CSF-02
  - CSF-03
duration: 25min
completed: 2026-05-07
---

# Phase 02 Plan 01: Canonical CSF Stage Identity Summary

**CSF runtime identity now stays canonical as `csf_*`, while lineage-local program paths remain compatible with established non-prefixed directories**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-07T08:05:00Z
- **Completed:** 2026-05-07T08:29:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Updated `SESSION_STAGE_PROGRAM_SPECS` so every CSF entry uses a canonical `csf_*` `stage_id`.
- Updated `STAGE_PROGRAM_SPECS` so generated CSF `stage_program.yaml` manifests record canonical CSF stage ids.
- Added explicit CSF canonical-id to local program directory mapping in `stage_program_relative_dir()`.
- Added focused tests locking canonical CSF session/scaffold identities and local program path compatibility.
- Updated CSF fixture program identity tests so CSF validation uses `csf_data_ready` rather than base `data_ready`.
- Documented that CSF canonical stage ids and non-prefixed lineage-local program directories intentionally coexist.

## Task Commits

1. **Canonical CSF stage identity and path compatibility** - pending final commit

## Files Created/Modified

- `runtime/tools/research_session.py` - CSF session stage specs now use canonical `csf_*` ids.
- `runtime/tools/stage_program_scaffold.py` - CSF scaffold manifests now write canonical `csf_*` ids while preserving local `program_dir` values.
- `runtime/tools/lineage_program_runtime.py` - CSF canonical ids resolve to non-prefixed lineage-local program dirs.
- `tests/runtime/test_lineage_program_runtime.py` - Locks CSF stage id specs, local path mapping, and materialized manifest identity.
- `tests/session/test_review_entry_preflight_scope.py` - Locks CSF session specs against identity downgrade.
- `tests/runtime/test_stage_program_identity.py` - Uses canonical CSF identity in CSF stage-program validation fixtures.
- `tests/runtime/test_csf_data_ready_auto_program.py` - Validates fixture CSF stage program with `csf_data_ready`.
- `docs/guides/qros-research-session-usage.md` - Documents CSF canonical stage ids and local program path compatibility.

## Decisions Made

- Keep compatibility for already-local non-prefixed CSF program ids in `stage_program_relative_dir()`; canonical `csf_*` ids are mapped, while base ids still resolve to the same local directories.
- Do not rename established lineage-local directories such as `program/cross_sectional_factor/data_ready`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `gsd-sdk query config-set workflow._auto_chain_active false` failed because the current SDK does not recognize that config key. This was a workflow compatibility issue, not a Phase 2 implementation blocker.

## User Setup Required

None.

## Verification

- `python -m pytest tests/runtime/test_lineage_program_runtime.py tests/session/test_review_entry_preflight_scope.py` -> 23 passed
- `python -m pytest tests/runtime/test_stage_program_identity.py tests/review/test_review_preflight_program_identity.py tests/review/test_review_engine_csf_contract_gates.py tests/runtime/test_csf_data_ready_auto_program.py` -> 30 passed
- `python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py` -> 9 passed
- `python runtime/scripts/run_verification_tier.py --tier smoke` -> 124 passed
- `python runtime/scripts/run_verification_tier.py --tier full-smoke` -> 176 passed

## Self-Check: PASSED

## Next Phase Readiness

Phase 3 can build on canonical CSF stage identity without resolving stage id drift between session state, scaffold manifests, review/preflight scope, and local program paths.

---
*Phase: 02-canonical-csf-stage-identity*
*Completed: 2026-05-07*
