# QROS Review Operations UX Design

## Context

The first review-proof-chain phase made ordinary QROS review fail closed:

- review request scope is normalized
- author materialization digests are order-stable and request-bound
- reviewer receipt is required before final review projection
- `review/final_review.yaml` must bind to active request scope, author digest, and stage program hash
- runtime projects canonical review result and write-scope audit artifacts without inventing reviewer judgment
- session state exposes proof-chain failures instead of collapsing them into generic pending states

That closes the core self-deception problem at the proof-chain layer. The second phase focuses on the operational experience around that stricter proof chain: when to launch a reviewer, what the reviewer receives, and how the main agent recovers when review is blocked.

The real `data_ready` and `csf_data_ready` friction showed that the reviewer lane was still being asked to discover too many low-value blockers: missing or placeholder artifacts, weak source provenance, stale handoff scope, thin stage programs, and unclear data coverage. Those are not adversarial reviewer judgments. They are deterministic readiness failures that should be caught before reviewer launch.

## Goal

Build a Review Operations UX layer that makes author-to-review operation deterministic and recoverable without weakening reviewer independence.

The target behavior is:

```text
author outputs complete
-> review operations snapshot
-> deterministic review-ready preflight
-> explicit user confirmation to launch reviewer
-> strict handoff package for independent reviewer
-> reviewer writes only review/final_review.yaml
-> runtime validates, projects, audits, closes, or routes recovery
```

## User-Approved Decisions

- Use a combined Review Operations UX design rather than separate one-off features.
- Implement in batches.
- Deterministic checks should run automatically.
- Reviewer launch, author-fix re-review, and failure routing should remain explicit confirmation boundaries.
- The first implementation batch should improve user-facing state and next-operation projection before changing reviewer launch mechanics.

## Non-Goals

- Do not replace adversarial review with preflight.
- Do not relax the strict proof-chain invariants from the first phase.
- Do not let runtime write or rewrite reviewer judgment.
- Do not add a new research stage.
- Do not rewrite all stage artifact contracts in this phase.
- Do not make `data_ready` a special review protocol. It may be the first hardening target, but the model must apply to all reviewable stages.

## Design Principles

### 1. Reviewer Is Not The First Completeness Checker

Reviewer effort should be reserved for high-value stage judgment: gate satisfaction, semantic drift, governance risk, and verdict. Required artifact existence, placeholder detection, stale request scope, source provenance, and basic data coverage should be checked before reviewer launch.

### 2. Disk Truth Beats Chat Memory

The main agent must not continue because the conversation suggests a stage is ready. It must use disk state, `stage_status`, `blocking_reason_code`, active request/context/digest, review proof-chain status, and stage-entry guards.

### 3. Explicit Handoff Only

Reviewer subagents should receive a bounded handoff package and must not inherit the launcher conversation as implicit context. The handoff must state what is reviewed, what is not reviewed, exact scope, exact digests, exact program path, and exact final-review schema expectations.

### 4. Recovery Is A Runtime Operation

Blocked review states must map to explicit next operations. The user and main agent should not need to infer whether the next step is author fix, request refresh, final-review rewrite, reviewer restart, failure handling, or next-stage confirmation.

## Architecture

### A. Review Operations Snapshot

Add a runtime-facing projection that summarizes the active review lane from existing truth sources. It should not create another review state machine. It should consume the proof-chain and eligibility signals already present in runtime.

Fields should include:

- `stage_id`
- `route_family`
- `review_eligible`
- `review_ready`
- `review_operation_state`
- `blocking_reason_code`
- `blocking_reason`
- `proof_chain_error`
- `author_outputs_stale_reason`
- `active_review_cycle_id`
- `request_present`
- `receipt_present`
- `final_review_present`
- `projected_result_present`
- `write_scope_audit_status`
- `requires_failure_handling`
- `recommended_next_operation`
- `recommended_skill`

The snapshot is the shared source for `qros-research-session`, `qros-progress`, and stage-specific review entry. Display text may differ by caller, but governance meaning must not diverge.

### B. Review-Ready Preflight

Run deterministic review-ready checks before asking the user to launch a reviewer.

The result is one of:

- `READY_TO_LAUNCH_REVIEWER`
- `AUTHOR_FIX_REQUIRED_BEFORE_REVIEW`
- `REQUEST_REFRESH_REQUIRED`
- `FAILURE_HANDLING_REQUIRED`

The preflight should check:

- required formal artifacts exist
- required provenance artifacts exist
- machine-readable outputs are not placeholders or contract-only stubs
- `artifact_catalog.md`, `field_dictionary.md`, and `run_manifest.json` exist when required
- lineage-local stage program exists and is not a thin wrapper
- `program_execution_manifest.json` binds current program hash and output refs
- source provenance fields are present for data-producing stages
- current author materialization digest matches any active request that is about to be reused
- stage-local semantic gates and deterministic preflight gates pass
- failure package or failure disposition has not already taken over the stage

For the first rollout, prioritize `data_ready`, `csf_data_ready`, and `tss_data_ready`, because they are most likely to suffer from fake data readiness and source provenance ambiguity.

### C. Reviewer Handoff Builder

After review-ready preflight passes and the user confirms reviewer launch, the runtime builds a strict handoff package.

The handoff should include:

- active request path
- reviewer receipt path
- `stage_contract_context.yaml`
- `stage_contract_context.md`
- exact `reviewed_artifact_paths`
- exact `reviewed_program_path`
- exact `reviewed_artifact_digest`
- exact `reviewed_program_digest`
- permitted read roots
- permitted write path: `review/final_review.yaml`
- stage-local focus checklist
- explicit note that prior chat context is not review truth
- final-review schema with concrete expected values where available

The reviewer should read `review/request/stage_contract_context.yaml` and `.md` as the review-cycle-local truth entrypoint instead of reconstructing stage gates from the generated review skill body.

### D. Review Recovery Router

Map blocked review states to a single recommended next operation.

Rules:

- `FIX_REQUIRED` means reviewer judgment requires author fix. Return to author lane within allowed modification boundaries, refresh author outputs, refresh request, and re-enter review confirmation.
- `AUTHOR_FIX_REQUIRED_BEFORE_REVIEW` means deterministic preflight blocked reviewer launch. Do not start reviewer.
- `AUTHOR_OUTPUTS_STALE` means the active proof chain no longer proves current author outputs. Refresh request/handoff before reviewer work continues.
- `REVIEW_SCOPE_MISMATCH` means the raw final review does not match active request scope. Require final-review rewrite or request refresh; do not project closure.
- `REVIEW_FORMAT_INVALID` means raw final review cannot be normalized without semantic changes. Require reviewer rewrite.
- `REVIEWER_SCOPE_VIOLATION` invalidates the current reviewer cycle. Do not keep the old verdict by deleting extra files; start a new cycle.
- `RETRY`, `NO-GO`, and `CHILD LINEAGE` route to formal failure handling, not ordinary author fix.
- `PASS` and `CONDITIONAL PASS` route to next-stage confirmation only after write-scope audit and closure are complete.

## User Experience

### Before Reviewer Launch

If preflight blocks review:

```text
Current stage is not ready for reviewer launch.
Reason: AUTHOR_FIX_REQUIRED_BEFORE_REVIEW
Fix author outputs first:
- <deterministic blocker>
Continue with qros-research-session after fixing; it will rerun review-ready preflight.
```

If preflight passes:

```text
Current stage is review-ready.
Deterministic checks passed.
Confirm whether to launch an independent reviewer for <stage_id>.
```

### During Review

If a reviewer is active:

```text
Waiting for independent reviewer to write review/final_review.yaml.
Reviewer is bound by receipt <review_cycle_id>.
```

### Blocked Review Cycle

If proof-chain validation fails:

```text
The active review cycle is invalid.
Reason: REVIEW_SCOPE_MISMATCH
Next operation: reviewer must rewrite review/final_review.yaml against the active request scope, or launcher must refresh request/handoff.
```

The UX must distinguish author content blockers from review proof-chain blockers. The main agent should not fix a proof-chain blocker by changing author outputs unless the router explicitly says the next operation is author fix.

## Batch Plan

### Batch 1: Review Operations Snapshot And Status Projection

Create the shared snapshot/projection layer and wire `qros-research-session`, progress, and review entry projections to it.

Acceptance criteria:

- stale active request does not display as generic pending
- malformed final review displays as format invalid
- scope mismatch displays as review scope mismatch
- `FIX_REQUIRED` displays as author fix required
- non-advancing verdict displays failure handling requirement
- callers use the same blocking reason code for the same disk state

### Batch 2: Review-Ready Preflight Before Reviewer Launch

Add automatic deterministic preflight before the user is asked to launch reviewer.

Acceptance criteria:

- `data_ready` with missing source provenance does not enter review confirmation
- placeholder machine artifacts do not enter review confirmation
- thin-wrapper stage program does not enter review confirmation
- coverage/time-window blocker does not launch reviewer
- review-ready pass is required before review confirmation is offered

### Batch 3: Reviewer Handoff Builder And Recovery Router

Improve handoff content and recovery projection after reviewer output exists.

Acceptance criteria:

- handoff includes exact expected final-review values
- reviewer handoff names stage contract context as the truth entrypoint
- reviewer write path is limited to `review/final_review.yaml`
- scope mismatch maps to final-review rewrite or request refresh
- write-scope violation maps to new reviewer cycle
- `FIX_REQUIRED` maps to author fix
- `RETRY`, `NO-GO`, and `CHILD LINEAGE` map to failure handling

## Error Taxonomy

### Author Or Stage Content Problems

These block reviewer launch:

- missing required artifact
- missing required provenance
- placeholder or empty machine artifact
- invalid data coverage
- missing source provenance
- thin wrapper stage program
- semantic gate fail
- deterministic preflight fail

Canonical operation:

```text
AUTHOR_FIX_REQUIRED_BEFORE_REVIEW
```

### Review Proof-Chain Or Handoff Problems

These invalidate the active review cycle or final review:

- stale request digest
- stale stage contract context
- final review scope mismatch
- final review digest mismatch
- final review program hash mismatch
- receipt mismatch
- reviewer identity collision
- write-scope violation

Canonical operations:

```text
REQUEST_REFRESH_REQUIRED
FINAL_REVIEW_REWRITE_REQUIRED
REVIEWER_RESTART_REQUIRED
```

### Reviewer Judgment Problems

These are actual reviewer verdict outcomes:

- `FIX_REQUIRED`
- `RETRY`
- `NO-GO`
- `CHILD LINEAGE`

Canonical operations:

```text
AUTHOR_FIX_REQUIRED
FAILURE_HANDLING_REQUIRED
```

## Testing Strategy

Focused tests:

- snapshot projection for each blocked review state
- progress/session parity for blocking reason codes
- review-ready preflight blocks missing artifacts, placeholder outputs, stale request, thin wrapper program, and missing source provenance
- handoff contains exact scope, digest, program path, receipt identity, and final-review schema
- recovery router maps proof-chain blockers separately from author content blockers
- `FIX_REQUIRED` does not enter failure handling
- `RETRY`, `NO-GO`, and `CHILD LINEAGE` do enter failure handling

Verification tiers:

- focused tests for each batch
- `python runtime/scripts/run_verification_tier.py --tier smoke`
- `python runtime/scripts/run_verification_tier.py --tier full-smoke` when stage flow, review orchestration, stage display, canonical stage naming, or review projection behavior changes

## Documentation Updates

When implemented, update:

- `docs/guides/qros-research-session-usage.md`
- `docs/guides/qros-review-shared-protocol.md`
- `docs/guides/qros-review-constraint-map.md`
- relevant `qros-*-author` and `qros-*-review` skills
- `skills/core/qros-research-session/SKILL.md`
- tests that lock user-facing status names, handoff text, and review operation states

## Success Criteria

Second phase is complete when:

- users do not need to know internal review command order
- main agent cannot launch reviewer before deterministic review-ready checks pass
- reviewer receives a bounded, explicit handoff and exact expected final-review bindings
- blocked review cycles map to explicit next operations
- author content blockers are not confused with proof-chain blockers
- `qros-research-session`, progress, and review entry agree on review blocking reason codes
- `data_ready` and route-specific data-ready stages no longer push basic source/data/provenance gaps into reviewer lane as first discoveries
