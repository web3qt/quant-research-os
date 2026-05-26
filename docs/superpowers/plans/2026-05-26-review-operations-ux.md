# Review Operations UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a shared Review Operations UX layer so QROS can distinguish author readiness blockers, review proof-chain blockers, reviewer judgment, and failure routing before launching or closing review.

**Architecture:** Add a focused `runtime/tools/review_operations.py` module for review operation snapshots, deterministic review-ready preflight projection, and recovery routing. Keep strict proof-chain validation in the existing review runtime modules, and make `research_session`, `progress_runtime`, and review handoff code consume the shared operation projection instead of each re-explaining review state.

**Tech Stack:** Python 3.11+, dataclasses, PyYAML, pytest, existing QROS runtime modules under `runtime/tools/`.

---

## File Structure

- Create `runtime/tools/review_operations.py`
  - Owns `ReviewOperationSnapshot`, `ReviewReadyPreflightResult`, `RecommendedReviewOperation`, stable operation constants, and pure projection helpers.
  - Must not import `runtime.tools.research_session` to avoid circular imports.
  - Imports only low-level modules such as `review_skillgen.adversarial_review_contract`, `review_skillgen.final_review_normalizer`, `review_skillgen.protocol_validator`, `review_skillgen.review_preflight`, `review_skillgen.reviewer_write_scope_audit`, `stage_evaluator`, and `lineage_program_runtime`.
- Modify `runtime/tools/research_session.py`
  - Delegates review substate and gate status projection to `review_operations`.
  - Keeps session-specific rendering and `SessionContext` construction in this file.
- Modify `runtime/tools/progress_runtime.py`
  - Reads the same operation snapshot for review blocking reason codes.
  - Remains read-only.
- Modify `runtime/tools/review_session_runtime.py`
  - Uses the shared review-ready preflight result before prepare/handoff.
  - Uses the shared handoff value projection for exact final-review schema values.
- Test `tests/review/test_review_operations.py`
  - New focused unit coverage for snapshot, operation routing, and preflight result mapping.
- Modify `tests/session/test_research_session_runtime.py`
  - Session behavior tests for user-facing `stage_status`, `blocking_reason_code`, and `next_action`.
- Modify `tests/session/test_qros_progress_runtime.py`
  - Progress parity tests.
- Modify `tests/session/test_research_session_assets.py` and `tests/review/test_review_cycle_prepare.py`
  - Handoff content tests.
- Update docs and skills:
  - `docs/guides/qros-research-session-usage.md`
  - `docs/guides/qros-review-shared-protocol.md`
  - `docs/guides/qros-review-constraint-map.md`
  - `skills/core/qros-research-session/SKILL.md`
  - `skills/core/qros-progress/SKILL.md`

## Task 1: Add Review Operations Snapshot Model

**Files:**
- Create: `runtime/tools/review_operations.py`
- Test: `tests/review/test_review_operations.py`

- [ ] **Step 1: Write failing tests for operation constants and basic no-review snapshot**

Add `tests/review/test_review_operations.py`:

```python
from pathlib import Path

from runtime.tools.review_operations import (
    OP_AWAITING_REVIEWER_COMPLETION,
    OP_REQUEST_REFRESH_REQUIRED,
    OP_REVIEW_NOT_STARTED,
    ReviewOperationSnapshot,
    build_review_operations_snapshot,
)


def test_review_operations_snapshot_for_missing_stage_dir_reports_not_started(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "topic_a"
    snapshot = build_review_operations_snapshot(
        lineage_root=lineage_root,
        stage_id="mandate",
        stage_dir=lineage_root / "01_mandate",
        reviewable=True,
    )

    assert isinstance(snapshot, ReviewOperationSnapshot)
    assert snapshot.stage_id == "mandate"
    assert snapshot.review_operation_state == OP_REVIEW_NOT_STARTED
    assert snapshot.request_present is False
    assert snapshot.receipt_present is False
    assert snapshot.final_review_present is False
    assert snapshot.recommended_next_operation is None


def test_review_operation_constants_are_stable() -> None:
    assert OP_REVIEW_NOT_STARTED == "REVIEW_NOT_STARTED"
    assert OP_AWAITING_REVIEWER_COMPLETION == "AWAITING_REVIEWER_COMPLETION"
    assert OP_REQUEST_REFRESH_REQUIRED == "REQUEST_REFRESH_REQUIRED"
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
python -m pytest tests/review/test_review_operations.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'runtime.tools.review_operations'`.

- [ ] **Step 3: Implement minimal snapshot dataclass and constants**

Create `runtime/tools/review_operations.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.tools.review_skillgen.adversarial_review_contract import FINAL_REVIEW_FILENAME

OP_REVIEW_NOT_STARTED = "REVIEW_NOT_STARTED"
OP_REVIEW_PREPARED = "REVIEW_PREPARED"
OP_AWAITING_REVIEWER_COMPLETION = "AWAITING_REVIEWER_COMPLETION"
OP_AUTHOR_FIX_REQUIRED = "AUTHOR_FIX_REQUIRED"
OP_AUTHOR_FIX_REQUIRED_BEFORE_REVIEW = "AUTHOR_FIX_REQUIRED_BEFORE_REVIEW"
OP_REQUEST_REFRESH_REQUIRED = "REQUEST_REFRESH_REQUIRED"
OP_FINAL_REVIEW_REWRITE_REQUIRED = "FINAL_REVIEW_REWRITE_REQUIRED"
OP_REVIEWER_RESTART_REQUIRED = "REVIEWER_RESTART_REQUIRED"
OP_FAILURE_HANDLING_REQUIRED = "FAILURE_HANDLING_REQUIRED"
OP_NEXT_STAGE_CONFIRMATION_REQUIRED = "NEXT_STAGE_CONFIRMATION_REQUIRED"


@dataclass(frozen=True)
class ReviewOperationSnapshot:
    stage_id: str
    stage_dir: Path
    reviewable: bool
    review_eligible: bool
    review_ready: bool
    review_operation_state: str
    blocking_reason_code: str | None
    blocking_reason: str | None
    proof_chain_error: str | None
    author_outputs_stale_reason: str | None
    active_review_cycle_id: str | None
    request_present: bool
    receipt_present: bool
    final_review_present: bool
    projected_result_present: bool
    write_scope_audit_status: str | None
    requires_failure_handling: bool
    recommended_next_operation: str | None
    recommended_skill: str | None


def build_review_operations_snapshot(
    *,
    lineage_root: Path,
    stage_id: str,
    stage_dir: Path,
    reviewable: bool,
    review_eligible: bool = False,
    review_ready: bool = False,
    proof_chain_error: str | None = None,
    author_outputs_stale_reason: str | None = None,
    requires_failure_handling: bool = False,
) -> ReviewOperationSnapshot:
    request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    receipt_path = stage_dir / "review" / "request" / "reviewer_receipt.yaml"
    final_review_path = stage_dir / "review" / FINAL_REVIEW_FILENAME
    projected_result_path = stage_dir / "review" / "result" / "adversarial_review_result.yaml"
    audit_path = stage_dir / "review" / "result" / "reviewer_write_scope_audit.yaml"

    if not reviewable or not stage_dir.exists():
        return ReviewOperationSnapshot(
            stage_id=stage_id,
            stage_dir=stage_dir,
            reviewable=reviewable,
            review_eligible=False,
            review_ready=False,
            review_operation_state=OP_REVIEW_NOT_STARTED,
            blocking_reason_code=None,
            blocking_reason=None,
            proof_chain_error=None,
            author_outputs_stale_reason=None,
            active_review_cycle_id=None,
            request_present=False,
            receipt_present=False,
            final_review_present=False,
            projected_result_present=False,
            write_scope_audit_status=None,
            requires_failure_handling=False,
            recommended_next_operation=None,
            recommended_skill=None,
        )

    return ReviewOperationSnapshot(
        stage_id=stage_id,
        stage_dir=stage_dir,
        reviewable=reviewable,
        review_eligible=review_eligible,
        review_ready=review_ready,
        review_operation_state=OP_REVIEW_PREPARED if request_path.exists() else OP_REVIEW_NOT_STARTED,
        blocking_reason_code=None,
        blocking_reason=None,
        proof_chain_error=proof_chain_error,
        author_outputs_stale_reason=author_outputs_stale_reason,
        active_review_cycle_id=None,
        request_present=request_path.exists(),
        receipt_present=receipt_path.exists(),
        final_review_present=final_review_path.exists(),
        projected_result_present=projected_result_path.exists(),
        write_scope_audit_status="PRESENT" if audit_path.exists() else None,
        requires_failure_handling=requires_failure_handling,
        recommended_next_operation=None,
        recommended_skill=None,
    )
```

- [ ] **Step 4: Run test and verify it passes**

Run:

```bash
python -m pytest tests/review/test_review_operations.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_operations.py tests/review/test_review_operations.py
git commit -m "feat: add review operations snapshot model"
```

## Task 2: Classify Proof-Chain Errors Into Review Operations

**Files:**
- Modify: `runtime/tools/review_operations.py`
- Test: `tests/review/test_review_operations.py`

- [ ] **Step 1: Write failing tests for proof-chain classification**

Append to `tests/review/test_review_operations.py`:

```python
from runtime.tools.review_operations import (
    OP_AUTHOR_FIX_REQUIRED_BEFORE_REVIEW,
    OP_FINAL_REVIEW_REWRITE_REQUIRED,
    OP_REVIEWER_RESTART_REQUIRED,
    classify_review_operation,
)


def test_classify_review_operation_maps_contract_stale_to_request_refresh() -> None:
    operation = classify_review_operation(
        proof_chain_error="REVIEW_CONTRACT_CONTEXT_STALE: active request is missing bound_author_materialization_digest",
        review_verdict=None,
        audit_error=None,
        preflight_blocked=False,
    )

    assert operation.operation == OP_REQUEST_REFRESH_REQUIRED
    assert operation.blocking_reason_code == "AUTHOR_OUTPUTS_STALE"


def test_classify_review_operation_maps_format_error_to_final_review_rewrite() -> None:
    operation = classify_review_operation(
        proof_chain_error="FORBIDDEN_FINAL_REVIEW_NORMALIZATION: reviewed_artifact_paths do not match active request scope",
        review_verdict=None,
        audit_error=None,
        preflight_blocked=False,
    )

    assert operation.operation == OP_FINAL_REVIEW_REWRITE_REQUIRED
    assert operation.blocking_reason_code == "REVIEW_SCOPE_MISMATCH"


def test_classify_review_operation_maps_audit_error_to_reviewer_restart() -> None:
    operation = classify_review_operation(
        proof_chain_error=None,
        review_verdict="PASS",
        audit_error="REVIEWER_WRITE_SCOPE_VIOLATION: reviewer wrote review/result/notes.yaml",
        preflight_blocked=False,
    )

    assert operation.operation == OP_REVIEWER_RESTART_REQUIRED
    assert operation.blocking_reason_code == "REVIEWER_SCOPE_VIOLATION"


def test_classify_review_operation_maps_preflight_block_to_author_fix_before_review() -> None:
    operation = classify_review_operation(
        proof_chain_error=None,
        review_verdict=None,
        audit_error=None,
        preflight_blocked=True,
    )

    assert operation.operation == OP_AUTHOR_FIX_REQUIRED_BEFORE_REVIEW
    assert operation.blocking_reason_code == "OUTPUTS_INVALID"
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
python -m pytest tests/review/test_review_operations.py -q
```

Expected: FAIL with `ImportError` for `classify_review_operation`.

- [ ] **Step 3: Implement classifier**

Add to `runtime/tools/review_operations.py`:

```python
@dataclass(frozen=True)
class RecommendedReviewOperation:
    operation: str
    blocking_reason_code: str | None
    blocking_reason: str


def classify_review_operation(
    *,
    proof_chain_error: str | None,
    review_verdict: str | None,
    audit_error: str | None,
    preflight_blocked: bool,
) -> RecommendedReviewOperation:
    if preflight_blocked:
        return RecommendedReviewOperation(
            operation=OP_AUTHOR_FIX_REQUIRED_BEFORE_REVIEW,
            blocking_reason_code="OUTPUTS_INVALID",
            blocking_reason="Deterministic review-ready preflight failed before reviewer launch.",
        )
    if proof_chain_error:
        if "REVIEW_CONTRACT_CONTEXT_STALE" in proof_chain_error or "author digest" in proof_chain_error.lower():
            return RecommendedReviewOperation(
                operation=OP_REQUEST_REFRESH_REQUIRED,
                blocking_reason_code="AUTHOR_OUTPUTS_STALE",
                blocking_reason=proof_chain_error,
            )
        if "reviewed_artifact_paths do not match" in proof_chain_error or "review scope" in proof_chain_error.lower():
            return RecommendedReviewOperation(
                operation=OP_FINAL_REVIEW_REWRITE_REQUIRED,
                blocking_reason_code="REVIEW_SCOPE_MISMATCH",
                blocking_reason=proof_chain_error,
            )
        if "FORBIDDEN_FINAL_REVIEW_NORMALIZATION" in proof_chain_error:
            return RecommendedReviewOperation(
                operation=OP_FINAL_REVIEW_REWRITE_REQUIRED,
                blocking_reason_code="REVIEW_FORMAT_INVALID",
                blocking_reason=proof_chain_error,
            )
        return RecommendedReviewOperation(
            operation=OP_REQUEST_REFRESH_REQUIRED,
            blocking_reason_code="ADVERSARIAL_REVIEW_PENDING",
            blocking_reason=proof_chain_error,
        )
    if audit_error:
        return RecommendedReviewOperation(
            operation=OP_REVIEWER_RESTART_REQUIRED,
            blocking_reason_code="REVIEWER_SCOPE_VIOLATION",
            blocking_reason=audit_error,
        )
    if review_verdict == "FIX_REQUIRED":
        return RecommendedReviewOperation(
            operation=OP_AUTHOR_FIX_REQUIRED,
            blocking_reason_code="AUTHOR_FIX_REQUIRED",
            blocking_reason="Reviewer requested author fixes before closure.",
        )
    if review_verdict in {"RETRY", "NO-GO", "CHILD LINEAGE"}:
        return RecommendedReviewOperation(
            operation=OP_FAILURE_HANDLING_REQUIRED,
            blocking_reason_code="FAILURE_HANDLING_REQUIRED",
            blocking_reason=f"Review verdict {review_verdict} requires formal failure handling.",
        )
    if review_verdict in {"PASS", "CONDITIONAL PASS"}:
        return RecommendedReviewOperation(
            operation=OP_NEXT_STAGE_CONFIRMATION_REQUIRED,
            blocking_reason_code="NEXT_STAGE_CONFIRMATION_REQUIRED",
            blocking_reason="Review passed and closure may proceed to next-stage confirmation after audit.",
        )
    return RecommendedReviewOperation(
        operation=OP_REVIEW_NOT_STARTED,
        blocking_reason_code=None,
        blocking_reason="No active review operation is blocking this stage.",
    )
```

- [ ] **Step 4: Run test and verify it passes**

Run:

```bash
python -m pytest tests/review/test_review_operations.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_operations.py tests/review/test_review_operations.py
git commit -m "feat: classify review operation blockers"
```

## Task 3: Wire Session Review Substate To Shared Operation Classification

**Files:**
- Modify: `runtime/tools/research_session.py`
- Test: `tests/session/test_research_session_runtime.py`

- [ ] **Step 1: Write failing session tests for operation-specific next actions**

Append to `tests/session/test_research_session_runtime.py` after `test_run_research_session_exposes_review_proof_chain_error`:

```python
def test_run_research_session_reports_request_refresh_operation_for_stale_active_request(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_reviewer_receipt(stage_dir)
    request_path = stage_dir / "review" / "request" / "adversarial_review_request.yaml"
    request_payload = yaml.safe_load(request_path.read_text(encoding="utf-8"))
    request_payload.pop("bound_author_materialization_digest", None)
    request_path.write_text(yaml.safe_dump(request_payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert status.blocking_reason_code == "AUTHOR_OUTPUTS_STALE"
    assert "Refresh" in status.next_action or "refresh" in status.next_action
    assert "review proof chain" in (status.blocking_reason or "")


def test_run_research_session_reports_final_review_rewrite_for_scope_mismatch(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_reviewer_receipt(stage_dir)
    request_payload = _review_request_payload(stage_dir)
    _write_yaml(
        stage_dir / "review" / "final_review.yaml",
        {
            "lineage_id": lineage_root.name,
            "stage_id": "mandate",
            "reviewer_identity": "reviewer-agent",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewed_artifact_paths": [],
            "reviewed_program_path": "program/mandate/run_stage.py",
            "reviewed_artifact_digest": request_payload["bound_author_materialization_digest"],
            "reviewed_program_digest": request_payload["author_program_hash"],
            "verdict": "PASS",
            "review_summary": "scope mismatch fixture",
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "rollback_stage": None,
            "downstream_permissions": [],
            "recommended_next_action": "rewrite final review",
        },
    )

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert status.blocking_reason_code == "REVIEW_SCOPE_MISMATCH"
    assert "rewrite" in status.next_action.lower() or "final_review.yaml" in status.next_action
```

- [ ] **Step 2: Run tests and verify the stricter next-action assertions fail if not yet wired**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py::test_run_research_session_reports_request_refresh_operation_for_stale_active_request tests/session/test_research_session_runtime.py::test_run_research_session_reports_final_review_rewrite_for_scope_mismatch -q
```

Expected: FAIL with an assertion mismatch showing that `next_action` still uses generic proof-chain repair wording.

- [ ] **Step 3: Import classifier and use it in `_review_substate`**

In `runtime/tools/research_session.py`, add:

```python
from runtime.tools.review_operations import (
    OP_FINAL_REVIEW_REWRITE_REQUIRED,
    OP_REQUEST_REFRESH_REQUIRED,
    OP_REVIEWER_RESTART_REQUIRED,
    classify_review_operation,
)
```

Inside `_review_substate`, after `proof_chain_error` and `audit_error` are computed, create:

```python
    operation = classify_review_operation(
        proof_chain_error=proof_chain_error,
        review_verdict=review_result.get("verdict") if isinstance(review_result, dict) else None,
        audit_error=audit_error,
        preflight_blocked=False,
    )
```

Replace generic proof-chain next actions with operation-specific wording:

```python
            if operation.operation == OP_REQUEST_REFRESH_REQUIRED:
                next_action = (
                    f"Refresh the active review request and handoff for {stage_base}, "
                    f"then relaunch a reviewer through {review_skill}."
                )
            elif operation.operation == OP_FINAL_REVIEW_REWRITE_REQUIRED:
                next_action = (
                    f"Ask the bound reviewer to rewrite review/{FINAL_REVIEW_FILENAME} against the active request scope, "
                    f"then rerun {review_skill}."
                )
            else:
                next_action = f"Repair the active review proof chain for {stage_base}, then rerun {review_skill}."
```

For audit errors, use:

```python
        if operation.operation == OP_REVIEWER_RESTART_REQUIRED:
            return (
                "reviewer_scope_violation",
                "REVIEWER_SCOPE_VIOLATION",
                f"{stage_base} reviewer write-scope audit failed: {audit_error}",
                f"Invalidate this reviewer cycle and launch a fresh reviewer through {review_skill}; do not reuse the old verdict.",
            )
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
python -m pytest tests/session/test_research_session_runtime.py::test_run_research_session_reports_request_refresh_operation_for_stale_active_request tests/session/test_research_session_runtime.py::test_run_research_session_reports_final_review_rewrite_for_scope_mismatch tests/review/test_review_operations.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/research_session.py tests/session/test_research_session_runtime.py tests/review/test_review_operations.py
git commit -m "feat: project review recovery operations in session"
```

## Task 4: Align Progress With Review Operations Projection

**Files:**
- Modify: `runtime/tools/progress_runtime.py`
- Test: `tests/session/test_qros_progress_runtime.py`

- [ ] **Step 1: Write failing progress parity test**

Add to `tests/session/test_qros_progress_runtime.py`:

```python
def test_progress_reports_same_review_scope_mismatch_as_session(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "btc_leads_alts"
    stage_dir = lineage_root / "01_mandate"

    _write_minimal_stage_outputs(stage_dir, stage="mandate")
    _write_adversarial_review_request(stage_dir, stage="mandate", program_dir="program/mandate")
    _write_reviewer_receipt(stage_dir)
    request_payload = _review_request_payload(stage_dir)
    _write_yaml(
        stage_dir / "review" / "final_review.yaml",
        {
            "lineage_id": lineage_root.name,
            "stage_id": "mandate",
            "reviewer_identity": "reviewer-agent",
            "reviewer_agent_id": "reviewer-child-agent",
            "reviewed_artifact_paths": [],
            "reviewed_program_path": "program/mandate/run_stage.py",
            "reviewed_artifact_digest": request_payload["bound_author_materialization_digest"],
            "reviewed_program_digest": request_payload["author_program_hash"],
            "verdict": "PASS",
            "review_summary": "scope mismatch fixture",
            "blocking_findings": [],
            "reservation_findings": [],
            "info_findings": [],
            "residual_risks": [],
            "allowed_modifications": [],
            "rollback_stage": None,
            "downstream_permissions": [],
            "recommended_next_action": "rewrite final review",
        },
    )

    payload = progress_status_payload(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert payload["blocking_reason_code"] == "REVIEW_SCOPE_MISMATCH"
    assert payload["stage_status"] == "review_scope_mismatch"
```

Ensure imports exist:

```python
from runtime.tools.progress_runtime import progress_status_payload
from tests.session.test_research_session_runtime import (
    _review_request_payload,
    _write_adversarial_review_request,
    _write_minimal_stage_outputs,
    _write_reviewer_receipt,
    _write_yaml,
)
```

- [ ] **Step 2: Run test**

Run:

```bash
python -m pytest tests/session/test_qros_progress_runtime.py::test_progress_reports_same_review_scope_mismatch_as_session -q
```

Expected: FAIL if progress still overrides the review blocking reason differently.

- [ ] **Step 3: Wire progress through session summary without private divergence**

In `runtime/tools/progress_runtime.py`, remove any branch that rewrites review proof-chain blocking reason codes after `summarize_session_status` already produced them. Keep review eligibility and failure routing overrides, but do not replace `REVIEW_SCOPE_MISMATCH`, `REVIEW_FORMAT_INVALID`, `AUTHOR_OUTPUTS_STALE`, or `REVIEWER_SCOPE_VIOLATION` with `OUTPUTS_INVALID`.

Add this guard before applying eligibility override inside `_read_only_session_status`:

```python
            protected_review_codes = {
                "REVIEW_SCOPE_MISMATCH",
                "REVIEW_FORMAT_INVALID",
                "AUTHOR_OUTPUTS_STALE",
                "REVIEWER_SCOPE_VIOLATION",
                "REVIEWER_UNBOUND",
            }
            if runtime_blocking_reason_code_override in protected_review_codes:
                return summarize_session_status(
                    lineage_id=lineage_root.name,
                    lineage_root=lineage_root,
                    lineage_mode=f"progress_{selection_mode}",
                    lineage_selection_reason=f"qros-progress selected {lineage_root.name} using {selection_mode} mode",
                    current_stage=current_stage,
                    current_route=current_research_route(lineage_root),
                    artifacts_written=[],
                    gate_status=gate_status,
                    next_action=next_action,
                    why_now=why_now,
                    open_risks=open_risks,
                    factor_role=route_contract["factor_role"],
                    factor_structure=route_contract["factor_structure"],
                    portfolio_expression=route_contract["portfolio_expression"],
                    neutralization_policy=route_contract["neutralization_policy"],
                    review_verdict=review_verdict,
                    requires_failure_handling=requires_failure_handling,
                    failure_stage=failure_stage,
                    failure_reason_summary=failure_reason_summary,
                    current_skill=current_skill_override,
                    why_this_skill=why_this_skill_override,
                    blocking_reason=blocking_reason_override,
                    resume_hint=resume_hint_override,
                    runtime_stage_status_override=runtime_stage_status_override,
                    runtime_blocking_reason_code_override=runtime_blocking_reason_code_override,
                    runtime_next_action_override=runtime_next_action_override,
                )
```

Before adding the protected-code branch, extract the final `summarize_session_status(...)` call into a local `_build_status()` closure and call it from both the protected-code branch and the ordinary path.

- [ ] **Step 4: Run progress and session focused tests**

Run:

```bash
python -m pytest tests/session/test_qros_progress_runtime.py::test_progress_reports_same_review_scope_mismatch_as_session tests/session/test_research_session_runtime.py::test_run_research_session_reports_final_review_rewrite_for_scope_mismatch -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/progress_runtime.py tests/session/test_qros_progress_runtime.py
git commit -m "fix: align progress review operation projection"
```

## Task 5: Add Review-Ready Preflight Result Helper

**Files:**
- Modify: `runtime/tools/review_operations.py`
- Test: `tests/review/test_review_operations.py`

- [ ] **Step 1: Write failing tests for review-ready result mapping**

Append to `tests/review/test_review_operations.py`:

```python
from runtime.tools.review_operations import (
    REVIEW_READY_AUTHOR_FIX_REQUIRED,
    REVIEW_READY_FAILURE_HANDLING_REQUIRED,
    REVIEW_READY_READY_TO_LAUNCH,
    map_review_ready_preflight_payload,
)


def test_map_review_ready_preflight_payload_passes_ready_to_launch() -> None:
    result = map_review_ready_preflight_payload(
        {
            "status": "PASS",
            "content_findings": [],
            "upstream_binding_findings": [],
            "research_preflight_findings": [],
        }
    )

    assert result.status == REVIEW_READY_READY_TO_LAUNCH
    assert result.blocking_findings == []


def test_map_review_ready_preflight_payload_blocks_author_fix() -> None:
    result = map_review_ready_preflight_payload(
        {
            "status": "FAIL",
            "content_findings": ["Missing required output: run_manifest.json"],
            "upstream_binding_findings": [],
            "research_preflight_findings": [],
        }
    )

    assert result.status == REVIEW_READY_AUTHOR_FIX_REQUIRED
    assert result.blocking_reason_code == "OUTPUTS_INVALID"
    assert result.blocking_findings == ["Missing required output: run_manifest.json"]


def test_map_review_ready_preflight_payload_blocks_failure_handling_for_failure_package() -> None:
    result = map_review_ready_preflight_payload(
        {
            "status": "FAIL",
            "content_findings": ["FAILURE_DISPOSITION_REQUIRED: latest failure package owns this stage"],
            "upstream_binding_findings": [],
            "research_preflight_findings": [],
        }
    )

    assert result.status == REVIEW_READY_FAILURE_HANDLING_REQUIRED
    assert result.blocking_reason_code == "FAILURE_DISPOSITION_REQUIRED"
```

- [ ] **Step 2: Run test**

Run:

```bash
python -m pytest tests/review/test_review_operations.py -q
```

Expected: FAIL with missing imports.

- [ ] **Step 3: Implement result helper**

Add to `runtime/tools/review_operations.py`:

```python
REVIEW_READY_READY_TO_LAUNCH = "READY_TO_LAUNCH_REVIEWER"
REVIEW_READY_AUTHOR_FIX_REQUIRED = "AUTHOR_FIX_REQUIRED_BEFORE_REVIEW"
REVIEW_READY_REQUEST_REFRESH_REQUIRED = "REQUEST_REFRESH_REQUIRED"
REVIEW_READY_FAILURE_HANDLING_REQUIRED = "FAILURE_HANDLING_REQUIRED"


@dataclass(frozen=True)
class ReviewReadyPreflightResult:
    status: str
    blocking_reason_code: str | None
    blocking_findings: list[str]


def map_review_ready_preflight_payload(payload: dict[str, Any]) -> ReviewReadyPreflightResult:
    findings = [
        str(item)
        for key in ("content_findings", "upstream_binding_findings", "research_preflight_findings")
        for item in (payload.get(key) or [])
    ]
    if payload.get("status") == "PASS" and not findings:
        return ReviewReadyPreflightResult(
            status=REVIEW_READY_READY_TO_LAUNCH,
            blocking_reason_code=None,
            blocking_findings=[],
        )
    if any("FAILURE_DISPOSITION_REQUIRED" in item or "FAILURE_HANDLING_REQUIRED" in item for item in findings):
        return ReviewReadyPreflightResult(
            status=REVIEW_READY_FAILURE_HANDLING_REQUIRED,
            blocking_reason_code="FAILURE_DISPOSITION_REQUIRED",
            blocking_findings=findings,
        )
    if any("REVIEW_CONTRACT_CONTEXT_STALE" in item or "author digest" in item.lower() for item in findings):
        return ReviewReadyPreflightResult(
            status=REVIEW_READY_REQUEST_REFRESH_REQUIRED,
            blocking_reason_code="AUTHOR_OUTPUTS_STALE",
            blocking_findings=findings,
        )
    return ReviewReadyPreflightResult(
        status=REVIEW_READY_AUTHOR_FIX_REQUIRED,
        blocking_reason_code="OUTPUTS_INVALID",
        blocking_findings=findings,
    )
```

- [ ] **Step 4: Run test**

Run:

```bash
python -m pytest tests/review/test_review_operations.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_operations.py tests/review/test_review_operations.py
git commit -m "feat: map review-ready preflight operations"
```

## Task 6: Require Review-Ready Preflight Before Review Confirmation For Data-Ready Stages

**Files:**
- Modify: `runtime/tools/research_session.py`
- Test: `tests/session/test_review_entry_preflight_scope.py`
- Test: `tests/session/test_research_session_runtime.py`

- [ ] **Step 1: Write failing test for `csf_data_ready` preflight blocker before review confirmation**

Add to `tests/session/test_review_entry_preflight_scope.py`:

```python
def test_csf_data_ready_review_confirmation_runs_review_ready_preflight(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs_root = tmp_path / "outputs"
    lineage_root = outputs_root / "csf_case"
    stage_dir = lineage_root / "02_csf_data_ready"
    _write_minimal_stage_outputs(stage_dir, stage="csf_data_ready")

    def _fake_run_review_preflight(*, explicit_context: dict[str, object]) -> dict[str, object]:
        assert Path(explicit_context["stage_dir"]) == stage_dir
        return {
            "stage": "csf_data_ready",
            "lineage_id": lineage_root.name,
            "status": "FAIL",
            "content_findings": ["run_manifest.json: source_data_provenance must bind real input data before review"],
            "upstream_binding_findings": [],
            "research_preflight_findings": [],
        }

    monkeypatch.setattr("runtime.tools.research_session.run_review_preflight", _fake_run_review_preflight)

    status = run_research_session(outputs_root=outputs_root, lineage_id=lineage_root.name)

    assert status.stage_status == "awaiting_author_fix"
    assert status.blocking_reason_code == "OUTPUTS_INVALID"
    assert "source_data_provenance" in (status.blocking_reason or "")
```

Add these imports at the top of `tests/session/test_review_entry_preflight_scope.py`:

```python
from pathlib import Path

import pytest

from runtime.tools.research_session import run_research_session
from tests.session.test_research_session_runtime import _write_minimal_stage_outputs
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
python -m pytest tests/session/test_review_entry_preflight_scope.py::test_csf_data_ready_review_confirmation_runs_review_ready_preflight -q
```

Expected: FAIL because `_review_entry_preflight_payload` currently returns `None` for post-mandate stages.

- [ ] **Step 3: Expand `_review_entry_preflight_payload` rollout set**

In `runtime/tools/research_session.py`, replace:

```python
    if _stage_base_name(current_stage) != "mandate":
        return None
```

with:

```python
    review_ready_preflight_stages = {
        "mandate",
        "data_ready",
        "csf_data_ready",
        "tss_data_ready",
    }
    if _stage_base_name(current_stage) not in review_ready_preflight_stages:
        return None
```

Keep the existing required-output guard:

```python
    if not all((author_formal_dir / name).exists() for name in spec.required_outputs):
        return None
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
python -m pytest tests/session/test_review_entry_preflight_scope.py tests/review/test_review_preflight_csf_data_ready_contract.py tests/review/test_review_preflight_tss_data_ready_contract.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/research_session.py tests/session/test_review_entry_preflight_scope.py
git commit -m "feat: run review-ready preflight for data-ready stages"
```

## Task 7: Block Review Cycle Prepare When Review-Ready Preflight Fails

**Files:**
- Modify: `runtime/tools/review_session_runtime.py`
- Test: `tests/review/test_review_cycle_prepare.py`

- [ ] **Step 1: Write failing prepare test**

Add to `tests/review/test_review_cycle_prepare.py`:

```python
def test_review_cycle_prepare_rejects_review_ready_preflight_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)

    def _fake_run_review_preflight(*, explicit_context: dict[str, object]) -> dict[str, object]:
        return {
            "stage": "mandate",
            "lineage_id": lineage_root.name,
            "status": "FAIL",
            "content_findings": ["Missing required output: run_manifest.json"],
            "upstream_binding_findings": [],
            "research_preflight_findings": [],
        }

    monkeypatch.setattr("runtime.tools.review_session_runtime.run_review_preflight", _fake_run_review_preflight)

    with pytest.raises(ValueError, match="AUTHOR_FIX_REQUIRED_BEFORE_REVIEW"):
        prepare_review_cycle_for_handoff(
            explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
            reviewer_identity="reviewer-agent",
            reviewer_session_id="review-session",
            launcher_session_id="launcher-session",
            launcher_thread_id="launcher-thread",
            reviewer_agent_id="reviewer-child-agent",
            host="codex",
        )

    assert not (stage_dir / "review" / "request" / "adversarial_review_request.yaml").exists()
```

- [ ] **Step 2: Run test**

Run:

```bash
python -m pytest tests/review/test_review_cycle_prepare.py::test_review_cycle_prepare_rejects_review_ready_preflight_failure -q
```

Expected: FAIL if prepare still writes request before preflight.

- [ ] **Step 3: Add preflight guard before `start_review_cycle` writes request**

In `runtime/tools/review_session_runtime.py`, import:

```python
from runtime.tools.review_operations import (
    REVIEW_READY_READY_TO_LAUNCH,
    map_review_ready_preflight_payload,
)
from runtime.tools.review_skillgen.review_preflight import run_review_preflight
```

Inside `prepare_review_cycle_for_handoff`, before calling `start_review_cycle`, add:

```python
    stage_dir = Path(explicit_context["stage_dir"])
    lineage_root = Path(explicit_context["lineage_root"])
    preflight_payload = run_review_preflight(
        explicit_context={
            "stage_dir": stage_dir,
            "lineage_root": lineage_root,
        }
    )
    preflight_result = map_review_ready_preflight_payload(preflight_payload)
    if preflight_result.status != REVIEW_READY_READY_TO_LAUNCH:
        details = "; ".join(preflight_result.blocking_findings[:3]) or "review-ready preflight failed"
        raise ValueError(f"{preflight_result.status}: {details}")
```

Because `prepare_review_cycle_for_handoff` accepts `explicit_context=None`, add the guard after the function has resolved `stage_dir` and `lineage_root` through the existing context-resolution path. The guard must always run before `start_review_cycle` writes `review/request/adversarial_review_request.yaml`.

- [ ] **Step 4: Run review-cycle tests**

Run:

```bash
python -m pytest tests/review/test_review_cycle_prepare.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_session_runtime.py tests/review/test_review_cycle_prepare.py
git commit -m "feat: block reviewer prepare on review-ready preflight failure"
```

## Task 8: Strengthen Reviewer Handoff With Exact Expected Values

**Files:**
- Modify: `runtime/tools/review_session_runtime.py`
- Test: `tests/session/test_research_session_assets.py`
- Test: `tests/review/test_review_cycle_prepare.py`

- [ ] **Step 1: Write handoff assertions**

Add this new test to `tests/session/test_research_session_assets.py`:

```python
def test_review_handoff_lists_exact_expected_final_review_bindings(tmp_path: Path) -> None:
    lineage_root, stage_dir = _prepare_mandate_stage(tmp_path)
    payload = prepare_review_cycle_for_handoff(
        explicit_context={"stage_dir": stage_dir, "lineage_root": lineage_root},
        reviewer_identity="codex-mandate-reviewer",
        reviewer_session_id="review-session-1",
        launcher_session_id="launcher-session-1",
        launcher_thread_id="launcher-thread-1",
        reviewer_agent_id="reviewer-child-1",
        host="codex",
    )

    request_payload = yaml.safe_load(
        (stage_dir / "review" / "request" / "adversarial_review_request.yaml").read_text(encoding="utf-8")
    )
    prompt = payload["reviewer_handoff_prompt"]

    assert "Do not infer review truth from prior chat" in prompt
    assert f"reviewed_artifact_digest: {request_payload['bound_author_materialization_digest']}" in prompt
    assert f"reviewed_program_digest: {request_payload['author_program_hash']}" in prompt
    assert "review/request/stage_contract_context.yaml" in prompt
    assert "review/request/stage_contract_context.md" in prompt
    assert "review/final_review.yaml" in prompt
    assert "review/result/adversarial_review_result.yaml" not in prompt
```

- [ ] **Step 2: Run test**

Run:

```bash
python -m pytest tests/session/test_research_session_assets.py::test_review_handoff_lists_exact_expected_final_review_bindings -q
```

Expected: FAIL until prompt has the exact sentence and no forbidden result-writing cue.

- [ ] **Step 3: Update `_reviewer_handoff_prompt` wording**

In `runtime/tools/review_session_runtime.py`, in `_reviewer_handoff_prompt`, add these lines near the top of the prompt:

```python
        "Do not infer review truth from prior chat. This handoff, review/request/*, author/formal/*, and the active stage program source are the review inputs.",
```

In the write-boundary section, keep:

```python
        "Write exactly one reviewer-owned file:",
        f"- {stage_dir.name}/review/{FINAL_REVIEW_FILENAME}",
```

Do not list `review/result/adversarial_review_result.yaml` or closure artifacts as reviewer write targets.

- [ ] **Step 4: Run handoff tests**

Run:

```bash
python -m pytest tests/session/test_research_session_assets.py tests/review/test_review_cycle_prepare.py::test_review_cycle_prepare_script_emits_handoff_prompt -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add runtime/tools/review_session_runtime.py tests/session/test_research_session_assets.py
git commit -m "fix: clarify reviewer handoff operation boundaries"
```

## Task 9: Document Review Operations UX

**Files:**
- Modify: `docs/guides/qros-research-session-usage.md`
- Modify: `docs/guides/qros-review-shared-protocol.md`
- Modify: `docs/guides/qros-review-constraint-map.md`
- Modify: `skills/core/qros-research-session/SKILL.md`
- Modify: `skills/core/qros-progress/SKILL.md`

- [ ] **Step 1: Add docs assertions**

Add to `tests/docs/test_install_docs.py`:

```python
def test_review_operations_ux_docs_explain_preflight_and_recovery() -> None:
    usage = (REPO_ROOT / "docs" / "guides" / "qros-research-session-usage.md").read_text(encoding="utf-8")
    shared = (REPO_ROOT / "docs" / "guides" / "qros-review-shared-protocol.md").read_text(encoding="utf-8")
    constraint_map = (REPO_ROOT / "docs" / "guides" / "qros-review-constraint-map.md").read_text(encoding="utf-8")

    assert "Review Operations Snapshot" in usage
    assert "AUTHOR_FIX_REQUIRED_BEFORE_REVIEW" in usage
    assert "REQUEST_REFRESH_REQUIRED" in usage
    assert "FINAL_REVIEW_REWRITE_REQUIRED" in shared
    assert "REVIEWER_RESTART_REQUIRED" in shared
    assert "review-ready preflight" in constraint_map
    assert "review/final_review.yaml" in constraint_map
```

- [ ] **Step 2: Run docs test**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py::test_review_operations_ux_docs_explain_preflight_and_recovery -q
```

Expected: FAIL until docs are updated.

- [ ] **Step 3: Update usage guide**

In `docs/guides/qros-research-session-usage.md`, add a section after the existing review discipline section:

```markdown
## Review Operations UX

`qros-research-session` now treats reviewer launch as a gated operation, not as a direct consequence of artifact presence.

Before launching a reviewer, runtime projects a Review Operations Snapshot and runs deterministic review-ready preflight. If the preflight finds missing artifacts, placeholder machine outputs, missing source provenance, thin stage programs, semantic gate failures, or stale handoff scope, the stage remains blocked with `AUTHOR_FIX_REQUIRED_BEFORE_REVIEW`, `OUTPUTS_INVALID`, or `REQUEST_REFRESH_REQUIRED`.

The ordinary next step is then to repair author outputs or refresh the review request through `qros-research-session`; do not start a reviewer to discover those deterministic blockers.

When review proof-chain artifacts are invalid, runtime uses separate recovery operations:

- `REQUEST_REFRESH_REQUIRED`: refresh active request and handoff before reviewer work continues.
- `FINAL_REVIEW_REWRITE_REQUIRED`: the bound reviewer must rewrite `review/final_review.yaml` against the active request scope.
- `REVIEWER_RESTART_REQUIRED`: the reviewer cycle is invalid, usually because write-scope audit failed; launch a new reviewer cycle.

These operations are distinct from reviewer judgment. `FIX_REQUIRED` returns to author fix; `RETRY`, `NO-GO`, and `CHILD LINEAGE` enter formal failure handling.
```

- [ ] **Step 4: Update shared review protocol**

In `docs/guides/qros-review-shared-protocol.md`, add:

```markdown
## Review Operations Recovery

Review recovery follows stable operations:

- `AUTHOR_FIX_REQUIRED_BEFORE_REVIEW`: deterministic review-ready preflight failed; do not launch reviewer.
- `REQUEST_REFRESH_REQUIRED`: active request or stage contract context no longer proves current author outputs.
- `FINAL_REVIEW_REWRITE_REQUIRED`: raw `review/final_review.yaml` cannot be accepted as written, usually due to scope or format mismatch.
- `REVIEWER_RESTART_REQUIRED`: the current reviewer cycle is invalid; do not reuse the old verdict.
- `FAILURE_HANDLING_REQUIRED`: verdict or failure package routes the lineage to formal failure handling.

Launcher agents must not convert these operations into informal judgment. They must follow the operation-specific recovery path.
```

- [ ] **Step 5: Update constraint map**

In `docs/guides/qros-review-constraint-map.md`, add this section after the first table that explains reviewer write ownership:

```markdown
## Review Operations Constraints

Review-ready preflight is deterministic author-lane validation. It may block reviewer launch for missing artifacts, placeholder machine outputs, missing provenance, stale handoff scope, or stage program identity failures, but it does not create a reviewer verdict.

The reviewer-owned write path remains `review/final_review.yaml`. Runtime-owned projection, closure, write-scope audit, and recovery routing remain outside the reviewer write scope.

Proof-chain recovery operations are launcher/runtime operations:

- `REQUEST_REFRESH_REQUIRED`: rebuild request and handoff before reviewer work continues.
- `FINAL_REVIEW_REWRITE_REQUIRED`: the bound reviewer must rewrite `review/final_review.yaml` against the active request.
- `REVIEWER_RESTART_REQUIRED`: invalidate the current reviewer cycle and launch a new one.
```

- [ ] **Step 6: Update skills**

In both `skills/core/qros-research-session/SKILL.md` and `skills/core/qros-progress/SKILL.md`, add concise bullets:

```markdown
- `AUTHOR_FIX_REQUIRED_BEFORE_REVIEW` means deterministic review-ready preflight failed; do not launch reviewer.
- `REQUEST_REFRESH_REQUIRED` means active request/handoff must be refreshed before reviewer work continues.
- `FINAL_REVIEW_REWRITE_REQUIRED` means the bound reviewer must rewrite `review/final_review.yaml`.
- `REVIEWER_RESTART_REQUIRED` means the current reviewer cycle is invalid and a new cycle is required.
```

- [ ] **Step 7: Run docs tests**

Run:

```bash
python -m pytest tests/docs/test_install_docs.py tests/skills/test_skill_tree.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add docs/guides/qros-research-session-usage.md docs/guides/qros-review-shared-protocol.md docs/guides/qros-review-constraint-map.md skills/core/qros-research-session/SKILL.md skills/core/qros-progress/SKILL.md tests/docs/test_install_docs.py
git commit -m "docs: explain review operations recovery"
```

## Task 10: Final Verification And Review

**Files:**
- Use this task for verification, review, and review-result follow-up only.

- [ ] **Step 1: Run focused review operations suite**

Run:

```bash
python -m pytest \
  tests/review/test_review_operations.py \
  tests/session/test_research_session_runtime.py \
  tests/session/test_qros_progress_runtime.py \
  tests/session/test_review_entry_preflight_scope.py \
  tests/review/test_review_cycle_prepare.py \
  tests/session/test_research_session_assets.py \
  -q
```

Expected: PASS.

- [ ] **Step 2: Run docs/bootstrap minimum**

Run:

```bash
python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py -q
```

Expected: PASS.

- [ ] **Step 3: Run smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
```

Expected: PASS.

- [ ] **Step 4: Run full-smoke**

Run:

```bash
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

Expected: PASS. This is required because the plan changes review orchestration, session/progress state projection, and review handoff behavior.

- [ ] **Step 5: Request code review**

Use `superpowers:requesting-code-review` against the branch base and current HEAD.

Review request summary:

```text
Implemented QROS Review Operations UX layer. Please review for bugs in review operation classification, session/progress parity, review-ready preflight gating, reviewer handoff boundaries, and recovery routing. Verify that preflight does not replace adversarial review and runtime does not invent reviewer judgment.
```

- [ ] **Step 6: Fix review findings or record clean review**

If reviewer reports blockers, create a new focused task inside this plan section with exact files, tests, and commands before editing. Run the relevant focused suite plus smoke/full-smoke when runtime behavior changed.

- [ ] **Step 7: Commit final verification note if docs changed during fixes**

When fixes from Step 6 change files, commit those exact paths:

```bash
git add runtime/tools/review_operations.py runtime/tools/research_session.py runtime/tools/progress_runtime.py runtime/tools/review_session_runtime.py docs/guides/qros-research-session-usage.md docs/guides/qros-review-shared-protocol.md docs/guides/qros-review-constraint-map.md tests/review/test_review_operations.py tests/session/test_research_session_runtime.py tests/session/test_qros_progress_runtime.py tests/session/test_review_entry_preflight_scope.py tests/review/test_review_cycle_prepare.py tests/session/test_research_session_assets.py tests/docs/test_install_docs.py
git commit -m "fix: address review operations ux review findings"
```

## Plan Self-Review

- Spec coverage: Task 1 and Task 2 cover Review Operations Snapshot and operation routing; Task 5 and Task 6 cover deterministic review-ready preflight; Task 7 prevents reviewer launch on preflight failure; Task 8 covers handoff exact values; Task 9 covers docs and skill UX; Task 10 covers verification and code review.
- Scope: This is one implementation plan because all batches build one shared review operations layer. Each task is independently testable and commit-sized.
- Type consistency: operation constants use uppercase string values; dataclasses use stable field names from the design spec; verdict spelling uses current contract values including `CHILD LINEAGE`.
- Verification: Runtime changes require focused tests, smoke, and full-smoke.
