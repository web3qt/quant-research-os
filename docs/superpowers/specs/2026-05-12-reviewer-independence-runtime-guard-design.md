# Reviewer Independence Runtime Guard Design

## Context

The May 2026 Claude Code CSF session exposed a narrower failure mode inside the
broader protected review state problem:

- the launcher/main thread edited `review/result/reviewer_findings.raw.yaml`
- the launcher converted `PASS` into `CLOSURE_READY_PASS`
- stale review directories were cleared and previous reviewer conclusions were reused
- author outputs changed after a review cycle, but old review evidence was still used
  to keep the lineage moving

This violates the QROS review contract. The reviewer may write raw findings, and
the deterministic closer may write canonical results and closure artifacts. The
launcher may not impersonate either role.

The existing `2026-05-11-qros-protected-review-state-design.md` defines the
general protected review state model. This document narrows the runtime design to
reviewer independence and old-review reuse prevention.

## Decision

Implement a Phase 1 runtime guard that treats each review cycle as a sealed
request/receipt/findings/closure transaction.

The runtime must not accept a review conclusion unless all of these are true:

1. `qros-review-cycle prepare` produced the active request, receipt, handoff
   manifest, write-scope baseline, and review runtime state.
2. `review/result/reviewer_findings.raw.yaml` is bound to the active receipt,
   active review cycle, active reviewer agent id, and current author digest.
3. `qros-review` is the only command that canonicalizes raw findings into
   `adversarial_review_result.yaml` and `review_findings.yaml`.
4. `qros-review` is the only command that writes closure artifacts.
5. If `author/formal/*` changes after prepare, all existing raw findings,
   canonical results, audits, and closure artifacts become stale.

The accepted recovery path is reset and re-review, not hand-editing governance
YAML.

## Protected Review Transaction

For an active review cycle, the protected transaction includes:

| Path | Owner | Runtime expectation |
| --- | --- | --- |
| `review/request/adversarial_review_request.yaml` | runtime | Defines active cycle, author digest, artifact scope, and handoff digest. |
| `review/request/reviewer_handoff_manifest.yaml` | runtime | Defines the exact reviewer-visible scope and launcher review-ready proof. |
| `review/request/reviewer_receipt.yaml` | runtime | Binds reviewer agent/session identity to the active cycle. |
| `review/request/reviewer_write_scope_baseline.yaml` | runtime | Freezes protected files before reviewer work. |
| `review/state/review_runtime_state.yaml` | runtime | Projection of active/closed review state; never independent proof. |
| `review/state/materialization_digest_ledger.yaml` | runtime cache | Cache only; cannot override fresh digest checks. |
| `review/result/reviewer_findings.raw.yaml` | reviewer | Reviewer-owned raw result for the active receipt-bound cycle. |
| `review/result/adversarial_review_result.yaml` | closer | Canonical result written by `qros-review`. |
| `review/result/review_findings.yaml` | closer | Human-readable normalized findings written by `qros-review`. |
| `review/result/reviewer_write_scope_audit.yaml` | closer | Audit written by `qros-review`. |
| `review/closure/latest_review_pack.yaml` | closer | Closure projection written only after passing checks. |
| `review/closure/stage_gate_review.yaml` | closer | Closure projection written only after passing checks. |
| `review/closure/stage_completion_certificate.yaml` | closer | Closure projection written only after passing checks. |

`review/review_cycle_trace.jsonl` remains append-only diagnostic evidence. It is
useful for postmortem but is not the Phase 1 source of authority.

## Runtime Guard Checks

### Active Cycle Binding

Before `qros-review` evaluates a cycle, it must verify:

- request, receipt, handoff manifest, baseline, and runtime state all reference
  the same `review_cycle_id`
- receipt `reviewer_agent_id` matches raw findings `reviewer_agent_id`
- raw findings `review_cycle_id` matches the active request
- handoff manifest digest in the request matches the current handoff manifest
- launcher review-ready path lists match the active request scope

Failure code:

```text
REVIEWER_FINDINGS_UNBOUND
```

### Current Author Digest Binding

The active request binds the reviewer to a specific author materialization digest.
Before accepting raw findings, the runtime must recompute a fresh digest of
current `author/formal/*` and required provenance.

If the fresh digest differs from the active request/state binding, the old review
cycle is stale.

Failure code:

```text
STALE_REVIEW_EVIDENCE
```

This must block closure even if the raw findings say `CLOSURE_READY_PASS`.

### Closer-Owned Canonical Files

If raw findings exist, `qros-review` may overwrite:

- `review/result/adversarial_review_result.yaml`
- `review/result/review_findings.yaml`
- `review/result/reviewer_write_scope_audit.yaml`

No other command should be relied on to produce those files. If these files exist
without a matching active raw findings binding, active request, receipt, and
runtime state, the guard must treat them as stale projection files.

Failure code:

```text
PROTECTED_STATE_DRIFT
```

### Closed Cycle Integrity

When `review_runtime_state.yaml` says the review is closed, the runtime must
verify:

- all closure artifacts exist
- closure artifacts carry the same `review_cycle_id`
- closure artifacts carry the same final verdict and review loop outcome
- closure artifacts refer to the same materialization digest used by the active
  request or canonical result
- no new `reviewer_findings.raw.yaml` exists for an already closed cycle

Failure code:

```text
CLOSURE_PROJECTION_DRIFT
```

### Result Write Scope

The reviewer write-scope audit must continue to reject changes outside
`review/result/*`, but it should also reject unexpected files inside
`review/result/*`.

Allowed result files:

- `reviewer_findings.raw.yaml` before closer canonicalization
- `adversarial_review_result.yaml`
- `review_findings.yaml`
- `reviewer_write_scope_audit.yaml`

Any extra result file must fail closure.

Failure code:

```text
REVIEWER_WRITE_SCOPE_VIOLATION
```

## Guarded Commands

The guard should run in these commands:

- `qros-review-cycle prepare`
- `qros-review`
- `qros-review-preflight`
- `qros-session`
- `qros-progress`
- `qros-check-stage-entry`

Command-specific behavior:

| Command | Guard behavior |
| --- | --- |
| `qros-review-cycle prepare` | Refuse to prepare a new cycle if an active stale cycle exists; require reset first. |
| `qros-review` | Refuse closure on unbound raw findings, stale author digest, protected state drift, or write-scope violation. |
| `qros-review-preflight` | Report stale review evidence before reviewer handoff. |
| `qros-session` | Do not advance next stage when review state is stale or closure projection drift exists. |
| `qros-progress` | Surface stable reason code and next action instead of summarizing stale review as pass. |
| `qros-check-stage-entry` | Block author/review entry if protected state drift would make the lane unsafe. |

## Recovery Path

The only normal recovery for stale review evidence is:

```bash
qros-review-cycle reset --archive-stale-cycle --stage <stage> --lineage-id <lineage_id>
qros-review-cycle prepare --stage <stage> --lineage-id <lineage_id> ...
```

Reset behavior:

- move current `review/request/*`, `review/result/*`, `review/closure/*`, and
  `review/state/*` into `review/archive/...`
- keep `author/formal/*` untouched
- clear active review state
- require a fresh reviewer run
- never copy old raw findings or canonical results into the new cycle

If the reviewed stage is already locked in `lineage_lock_ledger.yaml`, reset must
not mutate locked facts. Locked artifact drift remains `FROZEN_ARTIFACT_MUTATED`
and requires restore or child-lineage handling.

## Non-Goals

- Do not implement event sourcing in this phase.
- Do not infer reviewer identity from chat history.
- Do not permit the launcher to manually convert `PASS` to `CLOSURE_READY_PASS`.
- Do not let old reviewer findings prove changed author outputs.
- Do not teach agents to edit `lineage_lock_ledger.yaml`,
  `review_runtime_state.yaml`, or `materialization_digest_ledger.yaml` as a
  recovery strategy.

## Tests

Focused runtime tests should cover:

- raw findings with `PASS` instead of `CLOSURE_READY_PASS` fail with the legal enum
  message and do not create closure artifacts
- raw findings whose `reviewer_agent_id` differs from receipt fail with
  `REVIEWER_FINDINGS_UNBOUND`
- changing `author/formal/*` after prepare makes existing raw findings fail with
  `STALE_REVIEW_EVIDENCE`
- existing canonical result files without active raw findings/request/receipt fail
  with `PROTECTED_STATE_DRIFT`
- closed review state with missing or inconsistent closure artifacts fails with
  `CLOSURE_PROJECTION_DRIFT`
- `qros-review-cycle reset --archive-stale-cycle` archives stale proof files and
  requires a fresh reviewer run
- `qros-progress` reports the stable reason code instead of reporting stale PASS

Because this touches review/session/progress semantics, implementation should run:

```bash
python -m pytest tests/review/test_review_result_writer.py tests/review/test_review_runtime_state.py tests/review/test_adversarial_review_runtime.py tests/session/test_lineage_lock_session_status.py
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

For documentation-only edits to this spec, the repository minimum
documentation/bootstrap checks are sufficient.
