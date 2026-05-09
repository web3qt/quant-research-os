# QROS uv Python 3.12 Runtime Design

## Context

A QROS research session exposed a recurring failure mode: repo-local wrappers such as `.qros/bin/qros-progress` searched only `python` and `python3`. On the user's machine, both resolved to Python 3.9, while QROS runtime code requires Python 3.11+.

Claude Code then bypassed the stable wrappers and called `runtime/scripts/*` directly with a manually discovered Python 3.12 interpreter. That workaround kept the session moving, but it weakened the intended runtime boundary and made later provenance, review, and stage-gate behavior easier to bypass.

QROS should provision and lock its own runtime Python environment during install/update/bootstrap. Normal user-facing commands should use that environment instead of rediscovering system Python ad hoc.

## Decision

QROS runtime will standardize on Python 3.12 and use `uv` to provision and lock the runtime environment.

The managed environment lives inside the active research repo:

```text
.qros/.venv/
.qros/uv.lock
.qros/install-manifest.json
```

`qros-update` or bootstrap is responsible for creating or refreshing the environment. Ordinary commands such as `qros-progress`, `qros-session`, `qros-review`, and review/preflight wrappers must not install Python or dependencies as a side effect.

## Python Selection

All `.qros/bin/qros-*` wrappers should call one shared selection function from `qros-wrapper-lib`.

Selection order:

1. `QROS_PYTHON`, if set.
2. `.qros/.venv/bin/python`.
3. `uv python find 3.12`.
4. `python3.12` on `PATH`.

Every candidate must pass:

```python
import sys
raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)
```

If no candidate is valid, the wrapper fails closed with a message telling the user to run `qros-update` or the bootstrap command. It should not silently fall back to Python 3.9 or any unverified interpreter.

## Environment Provisioning

Bootstrap/update should:

1. Verify `uv` is installed and report a clear recovery message if missing.
2. Run `uv python install 3.12` when needed.
3. Create `.qros/.venv` with Python 3.12.
4. Sync QROS runtime dependencies from a locked dependency source.
5. Write `.qros/install-manifest.json` with:
   - `python_executable`
   - `python_version`
   - `runtime_lock_path`
   - `runtime_lock_digest`
   - `source_repo_path`
   - `source_git_commit`
   - `source_git_dirty`

The manifest records the environment used by the wrappers; it is not itself proof that a stage program ran.

## Locking Dependencies

Runtime dependencies should be lockfile-driven. The lock can be stored as `.qros/uv.lock` in the active research repo or copied from a canonical QROS lock artifact during install/update.

The lock digest must be recorded in `install-manifest.json`. Wrapper startup should verify that the lock digest still matches the installed environment metadata. If the lock changed, normal commands should fail closed and ask the user to refresh QROS instead of opportunistically syncing dependencies.

## Relationship To Provenance Drift

`QROS_ALLOW_PROVENANCE_DRIFT=1` remains a recovery escape hatch, not a normal execution mode.

The Python 3.12 managed environment reduces the main reason agents used provenance drift overrides: wrapper startup failure. After this change, routine use of `QROS_ALLOW_PROVENANCE_DRIFT=1` should be treated as a warning sign and documented only for explicit recovery operations.

## Relationship To A/B/C Hardening

This design is the prerequisite hardening layer for the larger governance fixes:

- A, provenance hardening: stage provenance can rely on a stable wrapper/runtime identity instead of arbitrary direct script invocation.
- B, review independence: review entrypoints can enforce reviewer identity and audit generation through managed wrappers.
- C, research semantic gates: preflight validators can run consistently under the locked dependency set.

This design does not by itself prevent forged `program_execution_manifest.json`, forged reviewer findings, proxy PnL, or factor-direction errors. It removes the environment instability that caused agents to bypass the intended entrypoints.

## Non-Goals

- Do not auto-install Python or dependencies during read-only commands.
- Do not require users to manually install Python 3.12 outside QROS if `uv` can provision it.
- Do not use this environment lock as stage execution provenance.
- Do not replace lineage immutable ledger, reviewer identity checks, or CSF semantic validators.

## Tests

Focused tests should cover:

- `qros-wrapper-lib` prefers `QROS_PYTHON` when it is Python 3.12.
- `.qros/.venv/bin/python` is selected before system Python.
- Python 3.9 candidates are rejected.
- `python3.12` is accepted when no managed venv exists.
- missing Python 3.12 produces a clear `qros-update` recovery message.
- wrapper selection logic is shared by all repo-local `qros-*` bin wrappers.
- install/update writes `python_version`, `python_executable`, and lock digest to `install-manifest.json`.

Because this affects user-facing runtime entrypoints, implementation should run:

```bash
python -m pytest tests/runtime/test_qros_wrapper_python_selection.py tests/bootstrap/test_project_bootstrap.py
python runtime/scripts/run_verification_tier.py --tier smoke
```

If the implementation also changes review/session gate behavior in the same patch, run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

## Success Criteria

After implementation:

- A fresh active research repo can run `.qros/bin/qros-progress` without relying on system `python3=3.9`.
- All `.qros/bin/*` wrappers use the same Python 3.12 selector.
- The managed environment and dependency lock are visible in `.qros/install-manifest.json`.
- Ordinary commands do not perform implicit installs.
- Agent workflows no longer need to call `runtime/scripts/*` directly just to avoid Python-version failures.
