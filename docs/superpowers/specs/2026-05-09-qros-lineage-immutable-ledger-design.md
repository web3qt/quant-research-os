# QROS Lineage Immutable Ledger Design

## Context

In a Claude Code QROS session, `csf_signal_ready_review` modified the frozen upstream mandate file:

- `01_mandate/author/formal/research_route.yaml`
- fields changed included `factor_role` and `neutralization_policy`

The same lineage later synchronized downstream route inheritance artifacts, so existing route digest checks could still pass. The current `reviewer_write_scope_audit.yaml` only protects files under the active stage directory, so it can pass even if a reviewer or launcher thread mutates upstream frozen artifacts outside that stage directory.

QROS needs a lineage-level immutability guard: once a stage has review closure, its formal artifacts and closure artifacts are immutable facts for the current lineage.

## Decision

Use a two-layer guard:

1. A lineage-level immutable ledger protects already reviewed upstream facts.
2. The existing reviewer write-scope audit continues to protect the current review cycle from reviewer write-scope violations.

These two checks answer different questions:

- Immutable ledger: did any already frozen artifact in this lineage change?
- Reviewer write-scope audit: did the reviewer write outside the allowed current-stage review result root?

This keeps upstream immutability out of reviewer-specific logic and makes the rule apply across author, review, progress, and closure entrypoints.

## Ledger Artifact

Add a lineage-local file:

```text
<lineage_root>/lineage_lock_ledger.yaml
```

Proposed shape:

```yaml
ledger_version: 1
lineage_id: btc_alt
locked_stages:
  mandate:
    locked_at: "2026-05-08T09:31:49Z"
    locked_at_review_cycle_id: "mandate-review-cycle-id"
    lock_reason: stage_review_closure
    files:
      - path: 01_mandate/author/formal/research_route.yaml
        sha256: "research-route-sha256"
        artifact_role: author_formal
      - path: 01_mandate/review/closure/stage_gate_review.yaml
        sha256: "stage-gate-review-sha256"
        artifact_role: review_closure
```

Paths are lineage-root relative. The ledger records digests, not replacement content.

## Lock Set

When a stage reaches PASS-like review closure, QROS locks:

- every required `author/formal/*` artifact for that stage
- every `review/closure/*` artifact for that stage
- required provenance files such as `program_execution_manifest.json` when they are part of the stage contract

For this design, PASS-like means the existing runtime already considers the stage eligible to advance or continue under a pass/retry closure. It excludes `NO_GO`, `CHILD_LINEAGE`, and any `FIX_REQUIRED` state.

Do not lock draft files, review request files, review result files, or transient runtime state.

The exact required formal/provenance set should come from the same contract sources already used by review runtime:

- `contracts/artifacts/*_artifacts.yaml`
- `contracts/stages/workflow_stage_gates.yaml`
- existing review scope construction where applicable

## Write Timing

`qros-review` writes or refreshes ledger entries immediately after closure artifacts are written.

Rules:

- If the stage is not PASS-like closure, do not lock it.
- If the stage is already locked and all digests match, the operation is idempotent.
- If the stage is already locked and any digest differs, fail with `FROZEN_ARTIFACT_MUTATED`.
- Never overwrite the old digest to make the ledger match a changed artifact.

## Validation Timing

Validate the lineage ledger before normal workflow actions:

- `qros-session` / `qros-progress` before status derivation
- `qros-check-stage-entry --lane author|review`
- `qros-review-preflight`
- `qros-review-cycle prepare`
- `qros-review` before closure

This prevents a mutated mandate from being normalized by later downstream artifacts.

## Failure Semantics

A ledger mismatch is an integrity stop, not an automatic child-lineage command.

Default behavior:

- hard block current action
- report the locked path, expected digest, observed digest, locked stage, and lock reason
- do not run author, review, preflight, closure, or downstream advancement
- do not auto-repair or synchronize downstream digests

Allowed next actions:

- restore the locked artifact to the ledger digest and continue current lineage
- if the user intentionally wants to keep the changed frozen fact, open a child lineage

Only intentional changes to already frozen upstream facts require child lineage. Current-stage author fixes before review closure do not.

## Example Behavior

If `csf_signal_ready_review` changes:

```text
01_mandate/author/formal/research_route.yaml
```

then later updates:

```text
03_csf_signal_ready/author/formal/route_inheritance_contract.yaml
```

the existing route inheritance digest may become internally consistent. The new ledger check must still fail because the mandate digest no longer matches the locked mandate entry.

The reported next action should be:

```text
Frozen upstream artifact changed. Restore 01_mandate/author/formal/research_route.yaml to the locked version, or open a child lineage if this route identity change is intentional.
```

## Error Handling

Use a stable machine-readable reason code:

```text
FROZEN_ARTIFACT_MUTATED
```

Recommended payload fields:

- `lineage_id`
- `locked_stage`
- `path`
- `expected_sha256`
- `observed_sha256`
- `lock_reason`
- `next_action`

This should surface through session/progress/review entrypoints without being treated as a normal stage retry.

## Tests

Focused tests should cover:

- writing `lineage_lock_ledger.yaml` after PASS-like closure
- idempotent ledger writes when digests match
- rejecting ledger overwrite when a locked artifact changed
- `qros-review-preflight` blocking when `01_mandate/author/formal/research_route.yaml` changes after mandate closure
- `qros-review-cycle prepare` blocking under the same condition
- `qros-session` / `qros-progress` surfacing `FROZEN_ARTIFACT_MUTATED`
- current-stage author edits before review closure remaining allowed
- reviewer write-scope audit continuing to pass or fail only for current-stage review write-scope behavior

Because this changes review / next-stage orchestration semantics, verification must include:

```bash
python -m pytest <focused tests>
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```
