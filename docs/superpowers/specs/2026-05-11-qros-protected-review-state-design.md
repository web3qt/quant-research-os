# QROS Protected Review State Design

## Context

Recent CSF session review showed a proof-chain discipline gap: an agent can keep a
lineage moving by manually editing governance state files that should represent
runtime-derived facts.

Observed risky edits included:

- `lineage_lock_ledger.yaml`
- `review/state/materialization_digest_ledger.yaml`
- `review/state/review_runtime_state.yaml`
- `review/result/reviewer_findings.raw.yaml`

Those edits can rescue a stuck session, but they weaken QROS semantics. Locks,
digests, review state, and raw reviewer findings should not be ordinary author
artifacts. They are runtime-owned governance state or reviewer-owned evidence.

This design borrows two patterns from adjacent agent workflows:

- Superpowers separates implementer and reviewer roles, and binds review to a
  specific work range instead of trusting the coordinator's session history.
- Get-shit-done treats project state as something to validate or rebuild through
  explicit workflow commands, not as a file the agent should hand-edit to move
  forward.

QROS already has part of this foundation: lineage immutable ledger checks,
reviewer receipts, reviewer write-scope audit, review runtime state, and
materialization digest caching. The design below strengthens those existing
mechanisms before introducing a larger event-sourced proof log.

## Decision

Implement protected review state in two phases.

Phase 1 is the required near-term hardening:

1. Mark protected governance files as runtime-owned or reviewer-owned.
2. Add a deterministic protected-state guard at review/session/progress entrypoints.
3. Treat `materialization_digest_ledger.yaml` as cache, not proof.
4. Require `reviewer_findings.raw.yaml` to be bound to the current reviewer receipt
   and current author digest.
5. Provide explicit repair commands that archive stale review cycles or rebuild
   runtime projections without preserving stale reviewer conclusions.

Phase 2 is optional follow-up:

1. Add an append-only proof event log.
2. Rebuild projection files from that log.
3. Fail preflight when projections and events disagree.

Phase 1 is intentionally smaller. It blocks the manual-adjustment failure mode
without changing every review lifecycle component at once.

## Protected Files

The protected files are:

| Path | Owner | Semantics |
| --- | --- | --- |
| `lineage_lock_ledger.yaml` | runtime | Immutable digest ledger for reviewed lineage facts. |
| `review/state/review_runtime_state.yaml` | runtime | Projection of the current active review cycle state. |
| `review/state/materialization_digest_ledger.yaml` | runtime cache | Cache for large artifact digest calculation; not independent proof. |
| `review/result/reviewer_findings.raw.yaml` | reviewer | Raw reviewer output for the active review cycle. |

Author skills must not write these files. The launcher/main thread must not edit
them to resolve a stuck review. Reviewer agents may write only
`review/result/reviewer_findings.raw.yaml`, and only for the active receipt-bound
cycle.

## Guarded Entry Points

The protected-state guard should run before normal work in these entrypoints:

- `qros-progress`
- `qros-research-session`
- `qros-check-stage-entry --lane author|review`
- `qros-review-preflight`
- `qros-review-cycle prepare`
- `qros-review`

The guard is a preflight/integrity check. If it fails, the command must stop
before authoring, review handoff, closure, or next-stage advancement.

## Guard Checks

### Lineage Lock Ledger

The existing immutable ledger check remains the authority for already reviewed
upstream artifacts.

The guard must:

- load `lineage_lock_ledger.yaml` when present
- recompute every locked file digest
- fail with `FROZEN_ARTIFACT_MUTATED` when any locked path is missing or changed
- never rewrite a locked digest to match changed content

This preserves the current invariant: changing a frozen upstream fact requires
restoration or child-lineage handling, not ledger adjustment.

### Review Runtime State

`review_runtime_state.yaml` is a projection, not the source of truth. The guard
must compare it to request, receipt, closure, and current author artifacts.

It should fail when:

- `active_review_cycle_id` does not match the current review request or receipt
- `review_bound_author_digest` does not match a fresh digest of current
  `author/formal` artifacts and required provenance
- state says review is closed but closure artifacts are missing or stale
- state says review is in progress but the active request/receipt pair is absent

Recommended error code:

```text
REVIEW_STATE_PROJECTION_DRIFT
```

### Materialization Digest Ledger

`materialization_digest_ledger.yaml` must be documented and treated as a cache.
It may accelerate digest calculation, but it cannot be the only evidence used by
preflight or closure.

The guard should support a fresh recomputation path. If cached metadata or cached
digest conflicts with current files, the runtime may either:

- ignore and refresh the cache during an explicit recompute, or
- fail with `MATERIALIZATION_CACHE_UNTRUSTED` when the command is not allowed to
  mutate review state.

The cache must never be hand-edited to make a stale author digest appear valid.

### Reviewer Findings

`reviewer_findings.raw.yaml` must be bound to the active review cycle.

Before closure, QROS must validate:

- `review/request/reviewer_receipt.yaml` exists and is valid
- findings `review_cycle_id` matches the receipt
- findings reviewer identity matches the receipt
- receipt-bound author digest equals the current author materialization digest
- reviewer verdict uses the canonical legal enum for closure handoff
- reviewer write-scope audit exists and passes

If any binding is missing or stale, fail with:

```text
REVIEWER_FINDINGS_UNBOUND
```

The recovery is to archive or reset the current review cycle and request a fresh
reviewer run. Old findings cannot prove changed author outputs.

## Repair Commands

Protected-state failures should not ask the user or agent to edit YAML. They
should point to explicit runtime commands.

Recommended commands:

```text
qros-review-state-validate
qros-review-state-rebuild --verify
qros-review-cycle reset --archive-stale-cycle
qros-lineage-lock-verify
```

Expected behavior:

- `qros-review-state-validate` reports projection drift without writing changes.
- `qros-review-state-rebuild --verify` rebuilds runtime projections from current
  request, receipt, closure, and author artifacts only when the proof chain is
  internally consistent.
- `qros-review-cycle reset --archive-stale-cycle` archives active request,
  result, closure, and state files, then returns the stage to a review-ready
  state requiring a fresh reviewer run.
- `qros-lineage-lock-verify` checks locked upstream facts and reports restore or
  child-lineage next actions.

Repair commands must not carry forward a previous reviewer conclusion onto new
author outputs.

## Failure Semantics

Protected-state failures are integrity stops, not ordinary author retries.

They should:

- hard block the current action
- print a stable machine-readable reason code
- identify the protected file and mismatched evidence
- recommend a runtime repair command
- avoid normal stage advancement or closure

Suggested reason codes:

| Code | Meaning |
| --- | --- |
| `FROZEN_ARTIFACT_MUTATED` | A locked lineage artifact changed after review closure. |
| `REVIEW_STATE_PROJECTION_DRIFT` | `review_runtime_state.yaml` disagrees with request, receipt, closure, or author digest. |
| `REVIEWER_FINDINGS_UNBOUND` | Raw reviewer findings are missing valid current-cycle receipt binding. |
| `MATERIALIZATION_CACHE_UNTRUSTED` | Digest cache cannot be trusted for current files. |
| `PROTECTED_STATE_DRIFT` | Generic protected-state failure when a narrower code does not apply. |

## Phase 2 Event Log

An append-only proof event log is still the cleaner long-term model, but it should
come after Phase 1.

Proposed future artifact:

```text
review/proof_chain.events.jsonl
```

Each event should include:

- `event_id`
- `prev_event_sha256`
- `event_type`
- `actor_role`
- `command`
- `runtime_lock_digest`
- `review_cycle_id`
- `input_digest`
- `output_digest`
- `target_paths`
- `timestamp`

Once this exists, `review_runtime_state.yaml` and selected ledgers can become
deterministic projections from the event log. Preflight should then fail when a
projection cannot be rebuilt from events.

Phase 2 is not required to close the immediate hand-editing gap.

## Tests

Focused tests for Phase 1 should cover:

- editing a locked formal artifact after closure makes progress/preflight fail
  with `FROZEN_ARTIFACT_MUTATED`
- changing `lineage_lock_ledger.yaml` to mask a changed artifact is rejected
- changing `review_runtime_state.yaml` to a closed state without matching closure
  artifacts fails with `REVIEW_STATE_PROJECTION_DRIFT`
- changing current author outputs after reviewer receipt invalidates existing raw
  findings with `REVIEWER_FINDINGS_UNBOUND`
- corrupting `materialization_digest_ledger.yaml` cannot make stale author
  outputs pass preflight
- `qros-review-cycle reset --archive-stale-cycle` archives stale active review
  files and requires a fresh reviewer run

Because this affects review/session/progress semantics, implementation should run:

```bash
python -m pytest tests/review/test_review_runtime_state.py tests/review/test_adversarial_review_runtime.py tests/runtime/test_lineage_lock_ledger.py
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

If only this design document changes, the minimum documentation/bootstrap checks
are sufficient.

## Non-Goals

- Do not replace all review state with event sourcing in Phase 1.
- Do not make manual YAML repair an accepted recovery path.
- Do not let old reviewer findings validate changed author outputs.
- Do not treat digest cache contents as formal proof.
- Do not broaden reviewer write scope beyond `review/result/reviewer_findings.raw.yaml`.
