# Phase 03 Validation Plan

## Required Commands

Focused runtime and skill tests:

```bash
python -m pytest tests/session/test_stage_entry_guard.py tests/skills/test_stage_entry_guard_guidance.py tests/bootstrap/test_project_bootstrap.py tests/bootstrap/test_install_runtime.py tests/bootstrap/test_native_skill_runtime_paths.py
```

Docs/bootstrap minimum:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py
```

Smoke:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Full smoke:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

## Pass Criteria

- Stage-specific author/review entry mismatch exits non-zero and gives an actionable `qros-research-session` recovery command.
- Matching author/review runtime states pass without writing artifacts.
- Installed runtime includes `qros-check-stage-entry`.
- Stage-specific skills require the guard before author/review work.
- Docs explain `qros-research-session` as the normal progression gate.
