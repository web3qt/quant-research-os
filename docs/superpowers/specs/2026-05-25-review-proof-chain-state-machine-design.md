# QROS Review Proof Chain State Machine Design

## Goal

This design tightens the shared QROS review proof-chain so ordinary stage review can be smoother without weakening adversarial reviewer independence.

The immediate trigger was a `csf_data_ready` run where review repeatedly stalled on stale digest detection, inconsistent required-output scopes, manual result projection, write-scope audit ordering, and receipt/result execution-mode mismatch. Those failures were mostly orchestration noise, not research-quality findings.

The target behavior is:

```text
author/formal artifacts
-> canonical review request
-> receipt-bound independent reviewer
-> reviewer writes only review/final_review.yaml
-> runtime writes normalized shadow
-> runtime projects adversarial_review_result.yaml
-> runtime runs write-scope audit
-> runtime writes closure artifacts
-> qros-session advances to next-stage confirmation or failure handling
```

Runtime may automate mechanical proof-chain projection, but it must not create or alter the reviewer's judgment.

## Non-Goals

- Do not change any stage artifact semantics such as `forward_return_panel.parquet`, `benchmark_suite_contract`, or data-ready feature contracts.
- Do not make `csf_data_ready` a special review path.
- Do not let preflight PASS replace adversarial review.
- Do not support ordinary closure from an unbound `review/final_review.yaml`.

## Shared Review State Machine

All stages use the same review lane state machine:

```text
review_not_started
-> review_preflight_passed
-> review_prepared
-> reviewer_bound
-> reviewer_handoff_delivered
-> final_review_received
-> final_review_normalized
-> result_projected
-> write_scope_audited
-> closure_written
```

Failure and branch states:

```text
author_outputs_stale
reviewer_unbound
review_scope_mismatch
review_format_invalid
reviewer_scope_violation
awaiting_author_fix
review_closed_nonadvancing
```

State meanings:

- `review_prepared`: active request exists and binds normalized scope plus author digest.
- `reviewer_bound`: `reviewer_receipt.yaml` exists and binds reviewer identity, reviewer session, reviewer agent id, execution mode, context source, and history inheritance.
- `final_review_received`: raw reviewer-owned `review/final_review.yaml` exists. This state is not closure-ready by itself.
- `final_review_normalized`: runtime has written a deterministic normalized shadow without changing review meaning.
- `result_projected`: runtime has projected a canonical `adversarial_review_result.yaml` from request, receipt, and normalized final review.
- `write_scope_audited`: reviewer write-scope audit passed.
- `closure_written`: closure artifacts have been written and the session may move to next-stage confirmation or failure routing.

## Canonical Review Scope

Introduce a shared `ReviewScope` concept used by review request, handoff manifest, stage contract context, protocol validation, digest calculation, and closure.

Fields:

```text
stage_id
required_artifact_paths
required_provenance_paths
stage_content_artifact_paths
stage_content_provenance_paths
upstream_binding_artifact_paths
upstream_binding_provenance_paths
required_program_dir
required_program_entrypoint
```

Path normalization rules:

- use POSIX relative paths
- remove trailing slashes
- reject absolute paths and `..`
- de-duplicate paths
- sort paths before digesting or comparing

Directory digest rules:

- directory paths are normalized without trailing slash
- directory content is recursively hashed in sorted relative-path order

Drift rules:

- Different path order is not drift.
- `shared_feature_base/` and `shared_feature_base` normalize to the same path.
- Required output set changes are drift.
- Artifact content changes are drift.
- Author output changes after prepare are drift.
- Files outside the active request scope are not silently added to the reviewed scope.

The implementation should add tests that keep `workflow_stage_gates.yaml`, stage evaluator specs, and review scope generation aligned, or make one of them a derived representation.

## Strict Receipt-Bound Review

Ordinary closure requires an active receipt.

Hard requirements:

- `reviewer_receipt.yaml` must exist before `review/final_review.yaml` can be consumed.
- `final_review.yaml.reviewer_agent_id` must match `reviewer_receipt.yaml.reviewer_agent_id`.
- `final_review.yaml.reviewer_identity` must match `reviewer_receipt.yaml.requested_reviewer_identity`.
- reviewer session id, execution mode, context source, and history inheritance are runtime-owned and come from receipt.
- reviewer identity must differ from author identity.
- reviewer agent/session must not be the launcher/main session for spawned-agent review.
- receipt must require `reviewer_context_source: explicit_handoff_only` and `reviewer_history_inheritance: none`.

If a raw final review exists without a valid active receipt, the state is `reviewer_unbound` and closure is rejected.

## Final Review Normalization

The reviewer-owned raw file remains immutable:

```text
review/final_review.yaml
```

Runtime may write a normalized shadow:

```text
review/result/final_review.normalized.yaml
```

Allowed non-semantic normalization:

- sort `reviewed_artifact_paths`
- serialize finding objects into stable strings
- fill missing nullable list fields with `[]`
- convert empty `rollback_stage` to `null`
- fill empty `allowed_modifications` and `downstream_permissions` with `[]`

Forbidden normalization:

- change `verdict`
- delete any finding
- move a finding between blocking, reservation, info, or residual risk classes
- generate downstream permissions
- downgrade blocker severity
- write or rewrite review summary
- claim review of artifacts outside the active request scope
- change reviewer identity or reviewer agent id

If forbidden normalization would be required, state becomes `review_format_invalid` or `review_scope_mismatch`, and the reviewer must rewrite the raw final review.

## Result Projection And Audit

`adversarial_review_result.yaml` is generated only from:

```text
active adversarial_review_request.yaml
active reviewer_receipt.yaml
review/result/final_review.normalized.yaml
```

Runtime may project proof-chain fields:

- review cycle id
- reviewer session id
- reviewer execution mode
- reviewer context source
- reviewer history inheritance
- reviewed program dir and entrypoint
- normalized reviewed artifact/provenance paths
- handoff manifest digest

Runtime must not generate reviewer judgment fields:

- verdict
- blocking findings
- reservation findings
- info findings
- residual risks
- downstream permissions
- review summary
- recommended action

After projection, runtime runs the write-scope audit automatically. Ordinary users and ordinary agents should not need to know the correct manual order for:

```text
qros-review
qros-audit-reviewer
qros-session --continue
```

Manual CLI entry points may remain for recovery and debugging, but they must use the same state machine and cannot bypass receipt binding, scope validation, normalization restrictions, or write-scope audit.

## User-Facing Status

`qros-session` and `qros-progress` should report explicit states rather than forcing the agent to infer from files:

- `awaiting_reviewer_completion`: active reviewer exists but no raw final review yet.
- `reviewer_unbound`: final review exists without valid receipt binding.
- `review_format_invalid`: final review cannot be normalized without semantic changes.
- `review_scope_mismatch`: reviewer did not bind to the active normalized request scope.
- `author_outputs_stale`: author outputs changed after prepare.
- `reviewer_scope_violation`: write-scope audit failed.
- `awaiting_author_fix`: reviewer returned `FIX_REQUIRED`.
- `review_closed_nonadvancing`: closure exists but verdict does not allow normal advancement.
- `next_stage_confirmation_pending`: closure passed and explicit next-stage confirmation is required.

## Safety Invariants

The design must preserve these invariants:

- Preflight cannot replace adversarial review.
- Main agent cannot close review using an unbound final review.
- Runtime cannot invent reviewer judgment.
- Raw reviewer output remains available for audit.
- Author artifact drift after prepare invalidates the review cycle.
- Reviewer scope must equal active request scope as a set.
- Write-scope audit must pass before closure.
- `FIX_REQUIRED` cannot advance to next-stage confirmation.
- `CONDITIONAL PASS` may advance only with its reservations and allowed modifications preserved.

## Test Plan

Focused tests should cover:

- unbound `final_review.yaml` is rejected
- receipt/final-review reviewer id mismatch is rejected
- reviewer scope missing, extra, or wrong artifact is rejected
- author output mutation after prepare is rejected
- required paths in different order produce the same digest
- `shared_feature_base/` and `shared_feature_base` normalize to the same path
- finding object is normalized to a stable string
- forbidden normalization attempts are rejected
- reviewer writes only `review/final_review.yaml`, then runtime writes normalized shadow, result, audit, and closure
- reviewer writes an extra protected file and audit fails
- `FIX_REQUIRED` routes to author fix
- `CONDITIONAL PASS` closes with reservations preserved

Verification requirements for implementation:

- focused review runtime/protocol/state tests
- docs/bootstrap minimal tests if docs or skills change
- `python runtime/scripts/run_verification_tier.py --tier smoke`
- `python runtime/scripts/run_verification_tier.py --tier full-smoke`

## Migration

Existing closed lineage stages continue to read closure artifacts as historical truth.

If a historical or manual stage has only `review/final_review.yaml` and no receipt, QROS must not auto-close it. It should report `reviewer_unbound` and direct the user to explicit manual recovery.

New ordinary review runs must use strict receipt-bound flow.

## Open Implementation Notes

- Prefer a single shared proof-chain module or state machine entry point even if implementation spans existing modules.
- Keep normalization deterministic and narrowly scoped.
- Add anti-regression tests before changing session behavior.
- Do not include data-ready artifact contract changes in this implementation.
