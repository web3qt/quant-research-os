# Phase 2 Research: Canonical CSF Stage Identity

**Phase:** 2 - Canonical CSF Stage Identity  
**Question:** What needs to be true before planning the CSF stage id and program path remediation?

## Findings

### Runtime session specs currently downgrade CSF identity

`runtime/tools/research_session.py` defines `SESSION_STAGE_PROGRAM_SPECS` keyed by canonical CSF stage names such as `csf_data_ready`, but the embedded `StageProgramSpec.stage_id` values are legacy base names:

- `csf_data_ready` -> `stage_id="data_ready"`
- `csf_signal_ready` -> `stage_id="signal_ready"`
- `csf_train_freeze` -> `stage_id="train_freeze"`
- `csf_test_evidence` -> `stage_id="test_evidence"`
- `csf_backtest_ready` -> `stage_id="backtest_ready"`
- `csf_holdout_validation` -> `stage_id="holdout_validation"`

This conflicts with review/preflight and artifact contracts that treat CSF stages as canonical `csf_*` route-specific contracts.

### Stage program scaffold has the same legacy identity drift

`runtime/tools/stage_program_scaffold.py` has `STAGE_PROGRAM_SPECS` entries keyed by canonical CSF names, but their `stage_id` fields also use base names. The `program_dir` values are already the desired lineage-local directories:

- `program/cross_sectional_factor/data_ready`
- `program/cross_sectional_factor/signal_ready`
- `program/cross_sectional_factor/train_freeze`
- `program/cross_sectional_factor/test_evidence`
- `program/cross_sectional_factor/backtest_ready`
- `program/cross_sectional_factor/holdout_validation`

The implementation should preserve those directory names while making `stage_id` canonical.

### Program path resolver currently breaks canonical CSF stage ids

`runtime/tools/lineage_program_runtime.py::stage_program_relative_dir()` currently returns:

```text
program/cross_sectional_factor/<stage_id>
```

for every cross-sectional factor stage. If callers pass the desired canonical `csf_data_ready`, it will look for:

```text
program/cross_sectional_factor/csf_data_ready
```

but the established lineage-local program directory is:

```text
program/cross_sectional_factor/data_ready
```

The resolver needs an explicit canonical-CSF-to-local-dir map.

### Existing tests cover adjacent behavior but not the canonical CSF contract

Useful existing anchors:

- `tests/runtime/test_lineage_program_runtime.py` already tests route-aware program path resolution and TSS stage program specs.
- `tests/session/test_review_entry_preflight_scope.py` reads `SESSION_STAGE_PROGRAM_SPECS` and will surface stage_dir/required output regressions.
- `tests/review/test_review_preflight_program_identity.py` and `tests/review/test_review_engine_csf_contract_gates.py` use `STAGE_PROGRAM_SPECS` to write review preflight fixtures.
- `tests/runtime/test_stage_program_identity.py` validates stage program manifests and is likely to catch mismatched manifest expectations.

Missing focused coverage:

- CSF `SESSION_STAGE_PROGRAM_SPECS[*].stage_id` must equal the canonical key.
- CSF `STAGE_PROGRAM_SPECS[*]["stage_id"]` must equal the canonical key.
- `stage_program_relative_dir("csf_data_ready", "cross_sectional_factor")` must return `program/cross_sectional_factor/data_ready`, not `program/cross_sectional_factor/csf_data_ready`.
- Generated/materialized stage program manifests for CSF stages must use canonical `stage_id` while keeping non-prefixed `program_dir`.

## Planning Implications

This should be a single tightly-scoped runtime identity plan, not split into independent waves, because all three requirements are coupled:

- Updating only specs makes lineage path lookup fail if canonical `stage_id` reaches the resolver.
- Updating only the resolver leaves scaffold/preflight manifests with legacy identity drift.
- Updating tests last risks preserving existing false-positive fixtures.

## Validation Architecture

Focused tests should run before broader smoke:

1. `python -m pytest tests/runtime/test_lineage_program_runtime.py tests/session/test_review_entry_preflight_scope.py`
2. `python -m pytest tests/runtime/test_stage_program_identity.py tests/review/test_review_preflight_program_identity.py tests/review/test_review_engine_csf_contract_gates.py`
3. `python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py`
4. `python runtime/scripts/run_verification_tier.py --tier smoke`
5. `python runtime/scripts/run_verification_tier.py --tier full-smoke`

The focused tests must include assertions that fail against the current old state:

- old `csf_data_ready -> data_ready` identity drift in `SESSION_STAGE_PROGRAM_SPECS`
- old `csf_data_ready -> data_ready` identity drift in `STAGE_PROGRAM_SPECS`
- old canonical CSF path resolution to `program/cross_sectional_factor/csf_data_ready`

## Risks

- Some fixture helpers may assume base-stage ids in generated `stage_program.yaml`; the plan should update fixtures/tests only where canonical CSF identity is the actual contract.
- TSS behavior must remain unchanged: legacy `data_ready` and canonical `tss_data_ready` path rules are separate from this CSF change.
- Review/preflight contract tests should validate both identity and established local path, not one at the expense of the other.
