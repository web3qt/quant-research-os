---
phase: 02
status: planned
created: 2026-05-07
---

# Phase 02 Validation Strategy

## Goal

Prove CSF stage identity is canonical as `csf_*` across session specs, scaffold specs, and lineage-local program runtime resolution, while preserving established non-prefixed CSF program directories.

## Blocking Dimensions

1. **Session spec identity**: `SESSION_STAGE_PROGRAM_SPECS` CSF entries use canonical `stage_id` equal to their `csf_*` key.
2. **Scaffold spec identity**: `STAGE_PROGRAM_SPECS` CSF entries write canonical `stage_id` into generated stage program manifests.
3. **Program path compatibility**: canonical CSF ids resolve to `program/cross_sectional_factor/<base>` directories such as `data_ready`.
4. **Review/preflight compatibility**: review preflight and review engine fixtures continue to accept canonical CSF identity with established local paths.
5. **Route non-regression**: TSS and route-neutral mandate program paths remain unchanged.

## Focused Commands

```bash
python -m pytest tests/runtime/test_lineage_program_runtime.py tests/session/test_review_entry_preflight_scope.py
python -m pytest tests/runtime/test_stage_program_identity.py tests/review/test_review_preflight_program_identity.py tests/review/test_review_engine_csf_contract_gates.py
```

## Required Broader Verification

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

## Acceptance Signal

All focused tests pass, smoke/full-smoke pass, and no test or doc continues to assert the old CSF identity mapping of `csf_data_ready -> data_ready`.
