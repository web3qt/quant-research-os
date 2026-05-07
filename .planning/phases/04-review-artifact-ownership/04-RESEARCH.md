# Phase 04 Research: Review Artifact Ownership

**Phase:** 04 -- Review Artifact Ownership
**Date:** 2026-05-07
**Status:** Ready for execution

## Scope

Phase 4 hardens the review proof chain so request, result, and closure artifacts cannot be hand-written by the launcher lane and still be treated as promotable independent review closure.

The phase is limited to review artifact ownership and recovery semantics. It does not change high-severity reservation escalation rules; those belong to Phase 5.

## Relevant Existing Mechanisms

- `runtime/scripts/review_cycle.py`
  - Provides the normal `qros-review-cycle prepare` entrypoint.
  - Calls `prepare_review_cycle_for_handoff()` and writes request, receipt, handoff prompt, and closer command.
- `runtime/tools/review_session_runtime.py`
  - Builds active review cycles.
  - Supports both `start_review_cycle(... execution_mode="spawned_agent")` and `start_review_session(... execution_mode="review_session")`.
  - Binds review cycles to author materialization digests and archives stale cycles.
- `runtime/tools/review_skillgen/adversarial_review_contract.py`
  - Writes `adversarial_review_request.yaml`, `reviewer_handoff_manifest.yaml`, and `reviewer_receipt.yaml`.
  - Validates request, receipt, manifest digest, reviewer mode, context isolation, and handoff contract.
- `runtime/tools/review_skillgen/review_result_writer.py`
  - Converts `reviewer_findings.raw.yaml` into canonical `adversarial_review_result.yaml`.
  - Still accepts an existing canonical `adversarial_review_result.yaml` when raw findings are absent.
- `runtime/tools/review_skillgen/protocol_validator.py`
  - Validates request, receipt, result, and write-scope audit before review evaluation.
- `runtime/tools/review_skillgen/reviewer_write_scope_audit.py`
  - Detects protected file edits outside `review/result`.
  - Does not prove that request/result/closure artifacts themselves were written by the intended runtime command.
- `runtime/tools/review_skillgen/closure_writer.py`
  - Writes `review/closure/latest_review_pack.yaml`, `stage_gate_review.yaml`, and `stage_completion_certificate.yaml`.
  - Does not attach writer metadata or validate pre-existing closure files.
- `runtime/tools/research_session.py` and `runtime/tools/stage_evaluator.py`
  - Treat closure as complete when proof-chain checks pass and `stage_completion_certificate.yaml` allows progress.
  - They do not currently validate closure artifact writer identity or closure payload digest.

## Gaps To Close

1. `review_session` and `local-review-session-*` receipts can currently produce `review_closed_pass` if the result validates. Phase 4 needs an explicit manual recovery contract before such a lane can produce promotable PASS.
2. Request artifacts carry a handoff manifest digest, but request/receipt themselves do not carry a stable runtime writer identity and self-digest that can detect launcher edits.
3. Canonical `adversarial_review_result.yaml` can still be accepted as a pre-existing file when no raw findings exist. This leaves a path for launcher-written canonical results.
4. Closure artifacts do not record deterministic writer metadata or source digests. A hand-written closure can look like a runtime closure if request/result/audit artifacts are otherwise valid.
5. Existing tests write canonical review artifacts directly in many fixtures. Phase 4 should update helpers to either use runtime helpers or attach the new explicit test-only/runtime ownership metadata.

## Design Choice

Add a small ownership layer for review artifacts:

- A new helper module, likely `runtime/tools/review_skillgen/artifact_ownership.py`, should compute canonical YAML digests while excluding the ownership block itself.
- Runtime-generated request, handoff manifest, receipt, canonical result, and closure payloads should carry an ownership block with at least:
  - `writer_owner`
  - `writer_command`
  - `writer_runtime`
  - `writer_identity`
  - `written_at`
  - `source_digests`
  - `payload_digest`
- The validator should reject payloads where ownership metadata is missing, the payload digest no longer matches, or source digests no longer match the active request/receipt/raw-result chain.

Add explicit recovery metadata:

- Normal review cycles remain `execution_mode: spawned_agent` with `recovery_status: normal_independent`.
- `execution_mode: review_session` defaults to `recovery_status: manual_recovery_unapproved`.
- A recovery command or contract, for example `review/request/manual_recovery_contract.yaml`, may mark a review session as `manual_recovery_approved`.
- `qros-review` must refuse promotable PASS for `local-review-session-*` or other review-session recovery lanes unless the approved recovery contract validates and is copied into closure payloads.

## Files To Change

- Add `runtime/tools/review_skillgen/artifact_ownership.py`.
- Update `runtime/tools/review_skillgen/adversarial_review_contract.py`.
- Update `runtime/tools/review_skillgen/review_result_writer.py`.
- Update `runtime/tools/review_skillgen/protocol_validator.py`.
- Update `runtime/tools/review_skillgen/closure_writer.py`.
- Update `runtime/tools/review_skillgen/review_engine.py`.
- Update `runtime/tools/research_session.py` and `runtime/tools/stage_evaluator.py` to reject invalid closure ownership.
- Update review scripts if needed:
  - `runtime/scripts/review_cycle.py`
  - `runtime/scripts/start_review_session.py`
  - `runtime/scripts/run_stage_review.py`
- Update tests under `tests/review/`, plus session/evaluator tests that consume closure state.
- Update `docs/guides/qros-review-shared-protocol.md` and related review skill guidance tests.

## Validation Architecture

Focused tests should cover four paths:

1. Normal independent spawned-agent PASS:
   - `qros-review-cycle prepare` writes owned request and receipt artifacts.
   - reviewer raw findings are canonicalized by `qros-review`.
   - closure artifacts carry writer metadata, source digests, reviewer execution mode, launcher owner, and `recovery_status: normal_independent`.
2. Local recovery block:
   - `start_review_session` or equivalent `local-review-session-*` review session writes a receipt.
   - raw findings request PASS.
   - `qros-review` exits non-zero or returns non-promotable state with no closure artifacts.
3. Explicit recovery metadata:
   - same recovery lane with a valid manual recovery contract.
   - closure is allowed, but closure records recovery status and contract digest.
4. Launcher-lane edit detection:
   - edit `review/request/*`, `review/result/adversarial_review_result.yaml`, or `review/closure/*` after generation.
   - `qros-review`, `run_research_session`, and/or `evaluate_stage` refuse promotion.

Because this phase touches review closure, display/progress state, and next-stage orchestration semantics, final execution must run focused tests, docs/bootstrap minimum, `smoke`, and `full-smoke`.
