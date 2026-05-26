from pathlib import Path

from runtime.tools.review_operations import (
    OP_AWAITING_REVIEWER_COMPLETION,
    OP_AUTHOR_FIX_REQUIRED_BEFORE_REVIEW,
    OP_FINAL_REVIEW_REWRITE_REQUIRED,
    OP_REQUEST_REFRESH_REQUIRED,
    OP_REVIEWER_RESTART_REQUIRED,
    OP_REVIEW_NOT_STARTED,
    ReviewOperationSnapshot,
    build_review_operations_snapshot,
    classify_review_operation,
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


def test_classify_review_operation_maps_contract_stale_to_request_refresh() -> None:
    operation = classify_review_operation(
        proof_chain_error="REVIEW_CONTRACT_CONTEXT_STALE: active request is missing bound_author_materialization_digest",
        review_verdict=None,
        audit_error=None,
        preflight_blocked=False,
    )

    assert operation.operation == OP_REQUEST_REFRESH_REQUIRED
    assert operation.blocking_reason_code == "AUTHOR_OUTPUTS_STALE"


def test_classify_review_operation_maps_bound_author_digest_to_request_refresh() -> None:
    operation = classify_review_operation(
        proof_chain_error="active request is missing bound_author_materialization_digest",
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
