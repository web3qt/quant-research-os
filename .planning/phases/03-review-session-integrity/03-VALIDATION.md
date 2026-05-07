---
phase: 03
status: planned
created: 2026-05-07
---

# Phase 03 Validation Strategy

## Goal

Prove manual/local review recovery cannot silently produce an ordinary promotable PASS, while preserving normal `spawned_agent` review closure and leaving explicit manual recovery auditable.

## Blocking Dimensions

1. **Independent reviewer path:** `spawned_agent` receipt + `CLOSURE_READY_PASS` still writes closure artifacts and records execution governance.
2. **Recovery block:** `review_session` receipt + `CLOSURE_READY_PASS` without `review/request/manual_recovery_contract.yaml` is rejected before closure artifacts are written.
3. **Explicit recovery contract:** `review_session` receipt + valid manual recovery contract may close PASS, but closure artifacts record it as manual recovery.
4. **Non-promoting recovery:** `review_session` receipt + `FIX_REQUIRED` remains accepted as non-advancing author-fix feedback.
5. **Documentation and skill truth:** shared protocol, user docs, core skills, and generated review skill template describe review-session recovery as downgraded governance.

## Focused Commands

```bash
python -m pytest tests/review/test_start_review_session.py tests/review/test_adversarial_review_runtime.py tests/review/test_review_engine.py tests/review/test_run_stage_review_script.py tests/review/test_review_result_writer.py
python -m pytest tests/review/test_adversarial_review_skill_generation.py tests/docs/test_install_docs.py
```

## Required Broader Verification

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

## Acceptance Signal

All focused tests pass, smoke/full-smoke pass, and no active docs or skills describe `review_session` as equivalent to the ordinary independent `spawned_agent` review path.
