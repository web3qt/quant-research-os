---
status: passed
phase: 02
phase_name: Canonical CSF Stage Identity
verified_at: 2026-05-07
requirements:
  CSF-01: passed
  CSF-02: passed
  CSF-03: passed
automated_checks:
  focused: passed
  docs_bootstrap: passed
  smoke: passed
  full_smoke: passed
schema_drift: passed
human_verification_required: false
---

# Phase 02 Verification: Canonical CSF Stage Identity

## Result

Passed. Phase 02 achieves the roadmap goal: CSF stage identity remains canonical as `csf_*` in runtime/session/scaffold/review identity, while established lineage-local program directories remain non-prefixed.

## Requirement Verification

| Requirement | Status | Evidence |
| --- | --- | --- |
| CSF-01 | Passed | `runtime/tools/research_session.py` uses canonical `csf_*` `stage_id` values for all six CSF `SESSION_STAGE_PROGRAM_SPECS` entries; `tests/session/test_review_entry_preflight_scope.py` locks this. |
| CSF-02 | Passed | `runtime/tools/lineage_program_runtime.py` maps canonical CSF ids such as `csf_data_ready` to local dirs such as `program/cross_sectional_factor/data_ready`; `tests/runtime/test_lineage_program_runtime.py` locks all six mappings. |
| CSF-03 | Passed | `tests/runtime/test_lineage_program_runtime.py`, `tests/session/test_review_entry_preflight_scope.py`, `tests/runtime/test_stage_program_identity.py`, and `tests/runtime/test_csf_data_ready_auto_program.py` lock scaffold/session/runtime identity behavior. |

## Must-Haves

- **CSF stage identity must remain canonical as `csf_*`:** Passed. Session specs, scaffold specs, generated manifests, and CSF validation fixtures now use canonical CSF ids.
- **Lineage-local CSF program directories must remain non-prefixed:** Passed. Runtime path resolution maps canonical CSF ids to existing `program/cross_sectional_factor/<base>` directories.
- **Tests must fail against the old identity downgrade:** Passed. Focused tests assert `spec.stage_id == stage_key` for CSF session/scaffold specs and assert canonical manifest `stage_id`.

## Automated Checks

- `python -m pytest tests/runtime/test_lineage_program_runtime.py tests/session/test_review_entry_preflight_scope.py` -> 23 passed
- `python -m pytest tests/runtime/test_stage_program_identity.py tests/review/test_review_preflight_program_identity.py tests/review/test_review_engine_csf_contract_gates.py tests/runtime/test_csf_data_ready_auto_program.py` -> 30 passed
- `python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py` -> 9 passed
- `python runtime/scripts/run_verification_tier.py --tier smoke` -> 124 passed
- `python runtime/scripts/run_verification_tier.py --tier full-smoke` -> 176 passed

## Review

Code review status: clean. See `02-REVIEW.md`.

## Residual Risk

`stage_program_relative_dir()` still accepts already-local non-prefixed CSF ids for compatibility. Runtime/session/scaffold/review identity now uses canonical `csf_*`, and focused tests lock that path, so this compatibility alias should not reintroduce session identity downgrade.

## Human Verification

None required.
