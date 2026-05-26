from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    if audit_error:
        return RecommendedReviewOperation(
            operation=OP_REVIEWER_RESTART_REQUIRED,
            blocking_reason_code="REVIEWER_SCOPE_VIOLATION",
            blocking_reason=audit_error,
        )
    if proof_chain_error:
        normalized_error = proof_chain_error.lower()
        scope_mismatch_phrases = (
            "reviewed_program_path does not match active request program",
            "reviewed_program_path does not match active request scope",
            "reviewed_program_digest does not match active request scope",
            "reviewed_artifact_digest does not match active request scope",
            "reviewed_artifact_paths do not match active request scope",
        )
        if "REVIEWER_UNBOUND" in proof_chain_error:
            return RecommendedReviewOperation(
                operation=OP_REVIEW_PREPARED,
                blocking_reason_code="REVIEWER_UNBOUND",
                blocking_reason=proof_chain_error,
            )
        if (
            "REVIEW_CONTRACT_CONTEXT_STALE" in proof_chain_error
            or "author digest" in normalized_error
            or "bound_author_materialization_digest" in normalized_error
        ):
            return RecommendedReviewOperation(
                operation=OP_REQUEST_REFRESH_REQUIRED,
                blocking_reason_code="AUTHOR_OUTPUTS_STALE",
                blocking_reason=proof_chain_error,
            )
        if any(phrase in normalized_error for phrase in scope_mismatch_phrases) or "review scope" in normalized_error:
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
    if review_verdict == "FIX_REQUIRED":
        return RecommendedReviewOperation(
            operation=OP_AUTHOR_FIX_REQUIRED,
            blocking_reason_code="AUTHOR_FIX_REQUIRED",
            blocking_reason="Reviewer requested author fixes before closure.",
        )
    if review_verdict in {"RETRY", "NO-GO", "CHILD LINEAGE", "PASS FOR RETRY"}:
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
