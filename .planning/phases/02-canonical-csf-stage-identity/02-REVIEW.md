---
status: clean
phase: 02
phase_name: Canonical CSF Stage Identity
depth: standard
files_reviewed: 8
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
reviewed_at: 2026-05-07
---

# Phase 02 Code Review

## Scope

Reviewed runtime, tests, and user-facing docs changed by Phase 02:

- `runtime/tools/research_session.py`
- `runtime/tools/stage_program_scaffold.py`
- `runtime/tools/lineage_program_runtime.py`
- `tests/runtime/test_lineage_program_runtime.py`
- `tests/session/test_review_entry_preflight_scope.py`
- `tests/runtime/test_stage_program_identity.py`
- `tests/runtime/test_csf_data_ready_auto_program.py`
- `docs/guides/qros-research-session-usage.md`

## Findings

No critical, warning, or info findings.

## Notes

- CSF `stage_id` values now stay canonical as `csf_*` in session specs and generated stage program manifests.
- `stage_program_relative_dir()` preserves established local program directories by mapping canonical CSF ids to base local names.
- TSS path behavior is unchanged and remains covered by existing route-aware path tests.
- The old CSF fixture identity in `test_stage_program_identity.py` was updated to canonical `csf_data_ready`.

## Verification Considered

- `python -m pytest tests/runtime/test_lineage_program_runtime.py tests/session/test_review_entry_preflight_scope.py`
- `python -m pytest tests/runtime/test_stage_program_identity.py tests/review/test_review_preflight_program_identity.py tests/review/test_review_engine_csf_contract_gates.py tests/runtime/test_csf_data_ready_auto_program.py`
- `python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py`
- `python runtime/scripts/run_verification_tier.py --tier smoke`
- `python runtime/scripts/run_verification_tier.py --tier full-smoke`
