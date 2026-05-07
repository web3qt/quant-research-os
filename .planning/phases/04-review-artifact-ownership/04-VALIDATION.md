---
phase: 04
slug: review-artifact-ownership
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-07
---

# Phase 04 -- Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/review/test_review_artifact_ownership.py tests/review/test_review_result_writer.py tests/review/test_review_cycle_prepare.py` |
| **Full suite command** | `python runtime/scripts/run_verification_tier.py --tier full-smoke` |
| **Estimated runtime** | focused: under 60s; smoke/full-smoke: repo tier dependent |

## Sampling Rate

- **After every task commit:** Run the focused command for touched review modules.
- **After every plan wave:** Run docs/bootstrap minimum and smoke.
- **Before `$gsd-verify-work`:** Run full-smoke.
- **Max feedback latency:** one focused test run per ownership mechanism.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| T1 | 04-01 | 1 | REV-01, REV-02 | T-04-01 | `local-review-session-*` cannot produce promotable PASS without approved recovery metadata. | unit/CLI | `python -m pytest tests/review/test_review_artifact_ownership.py tests/review/test_start_review_session.py` | yes | pending |
| T2 | 04-01 | 1 | CLOS-01, CLOS-04 | T-04-02 | `review/request/*` has runtime writer metadata and digest validation. | unit/CLI | `python -m pytest tests/review/test_review_cycle_prepare.py tests/review/test_adversarial_review_runtime.py` | yes | pending |
| T3 | 04-01 | 1 | CLOS-02, CLOS-04 | T-04-03 | Canonical result is generated from raw findings and prewritten canonical files are rejected unless owned by runtime. | unit/CLI | `python -m pytest tests/review/test_review_result_writer.py tests/review/test_run_stage_review_script.py` | yes | pending |
| T4 | 04-01 | 1 | CLOS-03, CLOS-04 | T-04-04 | Closure artifacts have writer/source digest metadata and edited closure files do not permit progression. | unit/session | `python -m pytest tests/review/test_closure_writer_context_modes.py tests/review/test_stage_evaluator.py tests/session/test_run_research_session_script.py` | yes | pending |
| T5 | 04-01 | 1 | REV-01, REV-02, CLOS-01..04 | T-04-05 | Docs and generated review skills name runtime-owned artifact boundaries. | docs/skill | `python -m pytest tests/review/test_adversarial_review_skill_generation.py tests/review/test_generated_skills_fresh.py tests/docs/test_install_docs.py` | yes | pending |

## Wave 0 Requirements

Existing pytest infrastructure and fixtures cover this phase. Add or update focused tests before implementation changes in the same execution wave.

## Manual-Only Verifications

All required Phase 4 behaviors should be covered by automated tests. Manual transcript review is useful for postmortem context but must not be a completion criterion.

## Required Commands

Focused review ownership tests:

```bash
python -m pytest tests/review/test_review_artifact_ownership.py tests/review/test_review_cycle_prepare.py tests/review/test_review_result_writer.py tests/review/test_start_review_session.py tests/review/test_run_stage_review_script.py tests/review/test_stage_evaluator.py
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

## Validation Sign-Off

- [x] All Phase 4 requirements have automated verification targets.
- [x] No manual-only behavior is required.
- [x] Smoke and full-smoke are mandatory because review closure semantics are changed.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** pending execution
