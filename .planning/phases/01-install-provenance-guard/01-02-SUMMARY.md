---
phase: 01-install-provenance-guard
plan: 01-02
subsystem: runtime
tags: [qros-wrapper, provenance-guard, qros-update, drift-check]
requires:
  - phase: 01-01
    provides: install manifest provenance fields
provides:
  - wrapper preflight for source path, expected source, and dirty-state drift
  - emergency provenance override and qros-update recovery diagnostics
affects: [qros-runtime, qros-session, qros-review, qros-update]
tech-stack:
  added: []
  patterns:
    - shared shell helper for repo-local wrapper provenance checks
key-files:
  created:
    - runtime/bin/qros-wrapper-lib
  modified:
    - runtime/bin/qros-session
    - runtime/bin/qros-review
    - runtime/bin/qros-review-cycle
    - runtime/bin/qros-review-preflight
    - runtime/bin/qros-validate-stage
    - runtime/bin/qros-update
    - runtime/bin/qros-progress
    - runtime/bin/qros-factor-diagnostics
    - runtime/bin/qros-signal-diagnostics
    - runtime/bin/qros-verify
    - runtime/bin/qros-agent-eval
    - runtime/bin/qros-audit-reviewer
    - runtime/bin/qros-start-review
    - tests/bootstrap/test_setup_script.py
    - tests/bootstrap/test_install_runtime.py
    - docs/guides/installation.md
    - docs/README.codex.md
key-decisions:
  - "Normal wrappers block provenance drift before script delegation."
  - "qros-update uses recovery mode so drift diagnostics remain reachable."
  - "QROS_ALLOW_PROVENANCE_DRIFT=1 is explicit emergency/manual recovery only."
patterns-established:
  - "All repo-local bin wrappers resolve runtime root through `qros-wrapper-lib`."
requirements-completed:
  - PROV-02
  - PROV-03
duration: 35min
completed: 2026-05-07
---

# Phase 01 Plan 02: Wrapper Provenance Guard Preflight Summary

**Repo-local QROS wrappers now run a shared provenance guard before delegating to session, review, validation, progress, update, and diagnostics scripts**

## Performance

- **Duration:** 35 min
- **Started:** 2026-05-07T08:25:00Z
- **Completed:** 2026-05-07T09:00:00Z
- **Tasks:** 3
- **Files modified:** 18

## Accomplishments

- Added `runtime/bin/qros-wrapper-lib` as the shared wrapper preflight implementation.
- Updated every `runtime/bin/qros-*` entry point to resolve `RUNTIME_ROOT` through the guard.
- Added blocking diagnostics for missing source path, `QROS_EXPECTED_SOURCE_REPO` mismatch, and clean-to-dirty source checkout drift.
- Kept `qros-update` in recovery mode so users still get drift diagnostics and recovery behavior.
- Documented `QROS_ALLOW_PROVENANCE_DRIFT=1` and `QROS_EXPECTED_SOURCE_REPO`.

## Task Commits

1. **Wrapper provenance guard preflight** - `50272cc` (feat)

**Plan metadata:** pending final phase metadata commit

## Files Created/Modified

- `runtime/bin/qros-wrapper-lib` - Shared provenance guard used by all wrappers.
- `runtime/bin/qros-*` - Wrapper entry points source the shared helper before runtime script delegation.
- `tests/bootstrap/test_setup_script.py` - Locks missing source path drift, expected-source mismatch, override, and qros-update recovery diagnostics.
- `tests/bootstrap/test_install_runtime.py` - Adds `qros-wrapper-lib` to installed runtime file expectations.
- `docs/guides/installation.md` - Documents wrapper provenance guard behavior.
- `docs/README.codex.md` - Adds concise troubleshooting guidance.

## Decisions Made

- Used a shared shell helper to avoid maintaining divergent guard logic across wrappers.
- `qros-update` uses recovery mode: it prints provenance drift diagnostics but is not hard-blocked by the guard itself.
- The emergency override is noisy by design and must be set explicitly.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `python -m pytest tests/bootstrap/test_setup_script.py tests/bootstrap/test_install_runtime.py tests/docs/test_install_docs.py` -> 21 passed

## Self-Check: PASSED

## Next Phase Readiness

Phase 1 can proceed to full verification. Later Python wrapper work can build on manifest `python_executable` / `python_version` without changing this provenance guard contract.

---
*Phase: 01-install-provenance-guard*
*Completed: 2026-05-07*
