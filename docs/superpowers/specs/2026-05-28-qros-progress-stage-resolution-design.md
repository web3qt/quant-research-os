# QROS Progress Stage Resolution Design

## Goal

Fix shared QROS stage resolution so `qros-progress` and `qros-research-session` report the latest true workflow state instead of being pulled back by stale upstream review artifacts.

The triggering case is a CSF lineage with these disk facts:

- `01_mandate`: completed with advancing review closure.
- `02_csf_data_ready`: completed with advancing review closure.
- `03_csf_signal_ready`: completed with advancing review closure.
- `04_csf_train_freeze`: completed with `review/closure/stage_completion_certificate.yaml` carrying an advancing `stage_status` or `final_verdict`, and the operator-facing next stage is `csf_test_evidence_confirmation_pending`.
- `05_csf_test_evidence`: waiting for confirmation.

Current runtime can incorrectly report `current_stage: mandate_review` because an old `01_mandate/review/request/adversarial_review_request.yaml` is malformed and lacks `review_cycle_id`. That old request is not the latest workflow fact and must not override downstream completed stages.

The target behavior is:

```text
latest real completed stage wins
-> qros-session and qros-progress share the same current_stage
-> closed upstream legacy review request defects do not rewind progress
-> active/highest-stage proof-chain defects still fail closed
```

## Non-Goals

- Do not add a `qros-progress`-only state resolver.
- Do not let placeholder directories, contract-only files, or missing provenance count as completed stages.
- Do not weaken proof-chain validation for the active or highest materialized stage.
- Do not allow non-advancing review verdicts such as `RETRY`, `NO-GO`, or `CHILD LINEAGE` to progress.
- Do not make CSF a special case beyond following the existing route-specific stage order.

## Shared Resolution Rule

`runtime.tools.research_session.detect_session_stage` remains the single truth for ordinary stage detection. `runtime.tools.progress_runtime` continues to consume that shared result rather than recomputing progress.

Stage detection should preserve the existing route-aware reverse scan:

```text
csf_holdout_validation
csf_backtest_ready
csf_test_evidence
csf_train_freeze
csf_signal_ready
csf_data_ready
mandate
```

The scan should distinguish two closure questions:

1. Is this stage the latest materialized stage whose review state must be actively interpreted?
2. Is this older stage already superseded by a later real stage and therefore only needed as historical progression evidence?

For the latest materialized stage, current proof-chain strictness stays in force. If the active request, receipt, final review, projected result, audit, or closure path is malformed, runtime should continue to report the appropriate review repair or failure state.

For an older upstream stage, a valid advancing `review/closure/stage_completion_certificate.yaml` is enough to prevent a stale `review/request/adversarial_review_request.yaml` from rewinding the lineage, as long as a later stage has real required outputs and provenance. The certificate verdict must be one of the existing advancing statuses: `PASS`, `CONDITIONAL PASS`, or `GO`.

This creates a deterministic precedence:

```text
later real stage materialization + provenance
beats older malformed review request
```

but does not create this unsafe shortcut:

```text
current malformed review request
beats proof-chain validation
```

## Implementation Shape

Add a small helper in `runtime/tools/research_session.py` for historical progression evidence, for example:

```text
_advancing_completion_certificate_exists(stage_dir: Path) -> bool
```

The helper should read only:

```text
<stage>/review/closure/stage_completion_certificate.yaml
```

and accept `stage_status` or `final_verdict` when it is an advancing status.

Then adjust the route-specific reverse scan so that after a later stage is recognized as materially present, earlier stage proof-chain defects cannot become the returned `current_stage`. The scan should still use existing required-output and provenance checks such as `stage_outputs_complete`.

`_review_closure_complete` can remain strict for active review interpretation. If implementation needs a second helper, name it so the distinction is explicit, for example:

```text
_review_closure_complete_for_active_stage
_historical_stage_advancing_closure_exists
```

Avoid naming that implies a malformed proof-chain is fully valid.

## Expected Current Stage

For the triggering lineage:

- If `04_csf_train_freeze` is PASS-closed and no `CONFIRM_NEXT_STAGE` has been recorded for it, current stage should be `csf_train_freeze_next_stage_confirmation_pending`.
- If the next-stage confirmation has been recorded and `05_csf_test_evidence` freeze groups are not confirmed, current stage should be `csf_test_evidence_confirmation_pending`.
- `mandate_review` should not be returned solely because an old mandate request is malformed after downstream CSF stages are already materialized and PASS-closed.

## Error Handling

If the highest materialized stage has malformed proof-chain state, runtime should keep the existing fail-closed behavior:

- report the stage's review repair state where appropriate
- preserve protected review blocking reason codes
- preserve failure handling for non-advancing verdicts
- do not silently convert a broken current review cycle into completed progress

If a later stage has directories or placeholder files but lacks required `author/formal` outputs or `program_execution_manifest.json`, it must not suppress an upstream active review state.

## Tests

Add focused tests that lock the shared behavior:

- `detect_session_stage` returns `csf_train_freeze_next_stage_confirmation_pending` when CSF stages 01-04 are materially complete and PASS-closed, even if `01_mandate/review/request/adversarial_review_request.yaml` is legacy malformed.
- `progress_status_payload` reports the same `current_stage` for the same lineage.
- After recording the next-stage confirmation for `csf_train_freeze`, both session and progress report `csf_test_evidence_confirmation_pending`.
- A malformed proof-chain on the highest materialized stage still blocks as review repair or active review state, not completed progress.
- A downstream placeholder-only stage does not suppress an upstream active review state.

Prefer using existing helpers from `tests/session/test_research_session_runtime.py`, `tests/session/test_qros_progress_runtime.py`, and `tests/helpers/lineage_program_support.py` instead of broad new fixtures.

## Documentation

Update user-facing docs only where they describe current-stage semantics. The minimum likely update is `docs/guides/qros-research-session-usage.md`, with a short note:

- current stage is determined by the latest real materialized stage and advancing closure
- closed legacy upstream review request defects do not rewind progress
- active/highest-stage proof-chain defects still fail closed

Do not describe this as a general permission to ignore review proof-chain validation.

## Verification

Because this changes shared stage flow and progress projection, implementation should run:

```bash
python -m pytest tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Final reporting must list the focused tests, smoke, and full-smoke results.
