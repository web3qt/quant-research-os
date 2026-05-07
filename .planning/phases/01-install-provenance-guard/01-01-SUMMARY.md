---
phase: 01-install-provenance-guard
plan: 01-01
subsystem: runtime
tags: [qros-install, provenance, manifest, drift-check]
requires: []
provides:
  - install manifest source checkout and Python interpreter provenance
  - setup check diagnostics for source path and dirty-state drift
affects: [qros-runtime, qros-installation, qros-update]
tech-stack:
  added: []
  patterns:
    - manifest provenance fields with deterministic setup checks
key-files:
  created: []
  modified:
    - runtime/tools/install_runtime.py
    - tests/bootstrap/test_install_runtime.py
    - docs/guides/installation.md
    - docs/README.codex.md
key-decisions:
  - "Phase 1 records Python interpreter metadata for audit only; wrapper interpreter preference remains later scope."
  - "Dirty status line-by-line drift is not strict when both installed and current states are dirty."
patterns-established:
  - "Install provenance diagnostics include exact installed/current fields and a recovery action."
requirements-completed:
  - PROV-01
  - PROV-03
duration: 20min
completed: 2026-05-07
---

# Phase 01 Plan 01: Install Manifest Provenance Contract Summary

**Install manifest provenance now records source checkout dirty state and Python interpreter metadata, with setup checks for source path and clean-to-dirty drift**

## Performance

- **Duration:** 20 min
- **Started:** 2026-05-07T08:05:00Z
- **Completed:** 2026-05-07T08:25:00Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- Added `source_git_dirty`, `source_git_status_short`, `python_executable`, and `python_version` to the install manifest.
- Extended `check_install()` to report source repo path drift and clean-to-dirty source checkout drift with recovery hints.
- Updated install/Codex docs to describe provenance fields and Phase 1 interpreter boundary.
- Added bootstrap tests for manifest fields and drift diagnostics.

## Task Commits

1. **Install provenance fields and drift checks** - `cb41b4b` (feat)

**Plan metadata:** pending final phase metadata commit

## Files Created/Modified

- `runtime/tools/install_runtime.py` - Builds extended manifest provenance and validates path/dirty-state drift.
- `tests/bootstrap/test_install_runtime.py` - Locks manifest field presence and setup-check drift diagnostics.
- `docs/guides/installation.md` - Documents provenance fields and drift recovery.
- `docs/README.codex.md` - Adds source path and dirty-state troubleshooting guidance.

## Decisions Made

- Interpreter fields are stored as provenance only in this plan; wrapper interpreter selection is intentionally deferred.
- `source_git_status_short` is recorded for audit, but strict line-by-line comparison is not enforced when both installed and current states are dirty.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `python -m pytest tests/bootstrap/test_install_runtime.py tests/docs/test_install_docs.py` -> 15 passed

## Self-Check: PASSED

## Next Phase Readiness

Wrapper preflight can now rely on manifest `source_repo_path`, `source_git_dirty`, and source checkout provenance fields.

---
*Phase: 01-install-provenance-guard*
*Completed: 2026-05-07*
