---
status: passed
phase: 01
phase_name: Install Provenance Guard
verified_at: 2026-05-07
requirements:
  PROV-01: passed
  PROV-02: passed
  PROV-03: passed
automated_checks:
  focused: passed
  docs_bootstrap: passed
  smoke: passed
  full_smoke: passed
schema_drift: passed
human_verification_required: false
---

# Phase 01 Verification: Install Provenance Guard

## Result

Passed. Phase 01 achieves the roadmap goal: installed QROS runtimes now detect and explain source repo path, commit, dirty-state, and interpreter provenance before normal session/review commands rely on installed runtime assets.

## Requirement Verification

| Requirement | Status | Evidence |
| --- | --- | --- |
| PROV-01 | Passed | `runtime/tools/install_runtime.py` writes `source_repo_path`, `source_git_commit`, `source_git_dirty`, `source_git_status_short`, `python_executable`, and `python_version`; `tests/bootstrap/test_install_runtime.py` locks these fields. |
| PROV-02 | Passed | `runtime/bin/qros-wrapper-lib` checks `QROS_EXPECTED_SOURCE_REPO` mismatch and missing source paths before wrapper delegation; `tests/bootstrap/test_setup_script.py` covers blocking and override behavior. |
| PROV-03 | Passed | `check_install()` reports commit/path/dirty-state drift; wrapper preflight blocks clean-to-dirty source drift and `qros-update` remains a recovery diagnostic path. |

## Must-Haves

- **Different source checkout must not silently drive session or review commands:** Passed. Normal wrappers call `qros_resolve_runtime_root(..., strict)` before runtime script delegation.
- **Dirty-source provenance must be visible before clean framework evidence is trusted:** Passed. Install manifest records dirty state and wrappers/check-install report clean-to-dirty drift.
- **Recovery must remain possible through `qros-update`:** Passed. `qros-update` uses recovery mode and prints provenance diagnostics instead of using the strict guard branch.
- **Emergency override must be explicit and auditable:** Passed. `QROS_ALLOW_PROVENANCE_DRIFT=1` prints an explicit warning before continuing.
- **Interpreter enforcement remains later scope:** Passed. Docs and summaries state interpreter fields are provenance only in Phase 01.

## Automated Checks

- `python -m pytest tests/bootstrap/test_install_runtime.py tests/docs/test_install_docs.py` -> 15 passed
- `python -m pytest tests/bootstrap/test_setup_script.py tests/bootstrap/test_install_runtime.py tests/docs/test_install_docs.py` -> 21 passed
- `python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py` -> 9 passed
- `python runtime/scripts/run_verification_tier.py --tier smoke` -> 124 passed
- `python runtime/scripts/run_verification_tier.py --tier full-smoke` -> 176 passed

## Review

Code review status: clean. See `01-REVIEW.md`.

## Residual Risk

`qros-update` can only fully recover a missing source checkout when an executable runtime source remains available. In a broken install with no reachable source runtime, it still emits recovery diagnostics but cannot delegate into `run_qros_update.py`. This is acceptable for Phase 01 because the guard no longer silently proceeds through normal session/review commands.

## Human Verification

None required.
