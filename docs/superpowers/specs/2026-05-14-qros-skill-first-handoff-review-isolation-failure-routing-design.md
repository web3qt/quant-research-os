# QROS Skill-First Handoff, Review Isolation, And Failure Routing Design

## Context

Recent real Codex sessions showed three coupled problems:

1. Normal users were still nudged toward backend recovery mechanics in some handoff paths.
2. Review cycles reused the same reviewer agent/session while still claiming isolated reviewer context.
3. CSF/TSS failure handling was not fully routed through the formal failure chain, so `FIX_REQUIRED`, `RETRY`, `NO-GO`, and `CHILD LINEAGE` could drift into mixed or manually improvised states.

This design closes those gaps together. The goal is not only to remove noisy user-facing command text, but to make the workflow state machine match what the runtime and review artifacts actually did.

## Decision

QROS should adopt a skill-first handoff contract and a stricter review/failure state machine:

- ordinary users only see the next QROS skill, not shell recovery commands
- every review cycle must be backed by a fresh reviewer identity unless the runtime explicitly declares reused context
- CSF/TSS failure stages must route through the formal failure handler chain
- failure disposition must be derived from the failure package and stage routing, not written ad hoc by the main author loop

## Goals

- Keep normal workflow guidance skill-based
- Prevent reviewer context reuse from being mislabeled as isolated
- Make CSF/TSS failure handling deterministic and route-complete
- Eliminate mixed states such as `NO_GO` recorded while review still claims `awaiting_author_fix`
- Preserve backend/debug recovery where needed, but keep it out of the ordinary user path

## Non-Goals

- Do not remove backend recovery primitives from the repo
- Do not change the underlying research route semantics
- Do not relax stage-entry guards or artifact contracts
- Do not turn failure handling into a free-form manual judgment loop

## Proposed Contract

### 1. Skill-first handoff

User-facing handoff fields are reduced to:

- `recommended_skill`
- `recommended_skill_reason`
- `handoff_hint`

These fields must point to skills, not shell commands. For normal progression:

- `*_next_stage_confirmation_pending` recommends `qros-research-session`
- `*_review_confirmation_pending` also recommends `qros-research-session`
- failure-disposition states recommend `qros-stage-failure-handler` or `qros-lineage-change-control`, depending on whether disposition is already recorded

Backend commands may still exist in machine payloads, but only as debug-only data. Text renderers must not surface them as the ordinary next action.

### 2. Reviewer isolation

Every review cycle must declare whether the reviewer is fresh or reused. The default is fresh.

Required review-cycle semantics:

- `qros-review-cycle prepare` creates a new `review_cycle_id`
- Codex-hosted review should spawn a new reviewer agent per cycle
- `reviewer_context_source` must describe the actual source of context
- `reviewer_history_inheritance` must match the actual inheritance mode
- if the runtime reuses a reviewer agent or its conversation, the review payload must say so explicitly

The runtime must fail closed if a cycle claims isolation while actually reusing reviewer context.

### 3. Failure routing

`qros-stage-failure-handler` becomes the single formal entry for failure routing.

It must cover both unprefixed and route-specific stages:

- `backtest_ready`
- `holdout_validation`
- `csf_data_ready`
- `csf_signal_ready`
- `csf_train_freeze`
- `csf_test_evidence`
- `csf_backtest_ready`
- `csf_holdout_validation`
- `tss_data_ready`
- `tss_signal_ready`
- `tss_train_freeze`
- `tss_test_evidence`
- `tss_backtest_ready`
- `tss_holdout_validation`

The handler must not stop at “generic stage failure” if the route-specific stage name exists. It must produce a stage-specific route to the correct failure skill, even when the downstream failure skill is shared across routes.

### 4. Failure disposition consistency

`FAILURE_DISPOSITION_REQUIRED` means the lineage is blocked until the formal failure package is completed.

`FAILURE_DISPOSITION_RECORDED` means the original lineage is closed for ordinary progression and can only continue through change control or child-lineage logic.

The runtime must not allow these to diverge:

- `review_state`
- `closure_written_at`
- `failure_disposition`
- `blocking_reason_code`

If the state says `NO_GO`, the surrounding review/failure metadata must also show a coherent closed failure path. If the state still says `awaiting_author_fix`, the lineage is not yet disposition-recorded.

## Architecture

### A. Handoff renderer

Shared renderers in `qros-session`, `qros-progress`, and `qros-review` should all use the same handoff projection.

Responsibilities:

- decide the next skill
- render a skill-only handoff
- keep backend debug fields out of normal output

### B. Review cycle registry

The review cycle preparation layer should record:

- reviewer identity
- reviewer session or agent id
- whether the cycle is fresh or reused
- context inheritance mode

This data becomes part of the review receipt and result audit trail.

### C. Failure router

The failure router should:

- inspect `stage_completion_certificate.yaml`
- inspect review verdict
- route route-specific stage names to the correct failure skill
- stop ordinary progression once failure handling is required

### D. Failure package builder

The failure package builder should own final failure disposition creation.

It must derive the final disposition from:

- failure classification
- post-retry decision
- review result
- route-specific stage contract

The main author loop must not write final failure disposition by itself.

## Data Flow

1. Runtime reads disk state for the current lineage.
2. The handoff projection selects the next skill.
3. Renderers show only skill-first guidance to normal users.
4. Review preparation creates a fresh reviewer cycle unless reuse is explicitly declared.
5. Review result and failure handler determine whether the lineage continues, retries, or closes.
6. If failure is recorded, only change control or child-lineage flow remains available.

## Error Handling

- If the current stage is still `*_next_stage_confirmation_pending`, the output must tell the user to continue `qros-research-session`, not to use a shell recovery step.
- If a review cycle claims `reviewer_history_inheritance: none` while reusing the same reviewer agent, fail closed.
- If a route-specific failure stage lands in the generic failure handler only, treat that as incomplete routing.
- If `FIX_REQUIRED` is present, do not allow direct final failure disposition without the formal failure package path.
- If `FAILURE_DISPOSITION_RECORDED` is present, block ordinary review and next-stage progression.

## Testing

The regression set should lock the following:

- `qros-session`, `qros-progress`, and `qros-review` do not print ordinary-user shell recovery commands
- `*_next_stage_confirmation_pending` recommends `qros-research-session`
- `*_review_confirmation_pending` also recommends `qros-research-session`
- CSF/TSS review and failure paths route to the correct skills
- reviewer receipts/results reflect actual context freshness or reuse
- failure disposition and review state cannot disagree on whether the lineage is still open
- `FIX_REQUIRED` does not skip the failure chain
- `NO_GO` and `CHILD LINEAGE` continue through change control instead of ordinary progression

At least one end-to-end session test should replay the real CSF backtest failure case that exposed the mixed-state behavior.

## Documentation Updates

Update the user-facing guidance to reflect the new contract:

- `docs/guides/qros-research-session-usage.md`
- `docs/guides/qros-review-shared-protocol.md`
- `docs/guides/installation.md`
- `skills/core/qros-research-session/SKILL.md`
- `skills/core/qros-progress/SKILL.md`
- `skills/csf_data_ready/qros-csf-data-ready-author/SKILL.md`
- `skills/backtest_ready/qros-backtest-failure/SKILL.md`
- `skills/failure_handling/qros-stage-failure-handler/SKILL.md`
- `skills/failure_handling/qros-lineage-change-control/SKILL.md`

The docs must distinguish normal skill handoff from backend recovery mechanics.

## Success Criteria

- Users only see skill-first handoffs in the normal path
- Review cycles cannot masquerade as isolated when they reuse context
- CSF/TSS failure handling routes through the right formal skill chain
- Failure disposition and review state remain internally consistent
- The real CSF backtest failure replay no longer shows mixed-state drift
