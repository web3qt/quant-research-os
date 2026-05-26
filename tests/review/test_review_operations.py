from pathlib import Path

import pytest

from runtime.tools.review_operations import (
    OP_AWAITING_REVIEWER_COMPLETION,
    OP_AUTHOR_FIX_REQUIRED_BEFORE_REVIEW,
    OP_FAILURE_HANDLING_REQUIRED,
    OP_FINAL_REVIEW_REWRITE_REQUIRED,
    OP_REQUEST_REFRESH_REQUIRED,
    OP_REVIEWER_RESTART_REQUIRED,
    OP_REVIEW_NOT_STARTED,
    OP_REVIEW_PREPARED,
    REVIEW_READY_AUTHOR_FIX_REQUIRED,
    REVIEW_READY_FAILURE_HANDLING_REQUIRED,
    REVIEW_READY_READY_TO_LAUNCH,
    REVIEW_READY_REQUEST_REFRESH_REQUIRED,
    ReviewOperationSnapshot,
    build_review_operations_snapshot,
    classify_review_operation,
    map_review_ready_preflight_payload,
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


def test_classify_review_operation_maps_stale_review_cycle_to_request_refresh() -> None:
    operation = classify_review_operation(
        proof_chain_error=(
            "author/formal outputs or provenance changed after adversarial_review_request.yaml was issued; "
            "review cycle is stale"
        ),
        review_verdict=None,
        audit_error=None,
        preflight_blocked=False,
    )

    assert operation.operation == OP_REQUEST_REFRESH_REQUIRED
    assert operation.blocking_reason_code == "AUTHOR_OUTPUTS_STALE"


@pytest.mark.parametrize(
    "proof_chain_error",
    [
        "FORBIDDEN_FINAL_REVIEW_NORMALIZATION: reviewed_program_path does not match active request program",
        "FORBIDDEN_FINAL_REVIEW_NORMALIZATION: reviewed_program_digest does not match active request scope",
        "FORBIDDEN_FINAL_REVIEW_NORMALIZATION: reviewed_artifact_digest does not match active request scope",
        "FORBIDDEN_FINAL_REVIEW_NORMALIZATION: reviewed_artifact_paths do not match active request scope",
        "REVIEW_CONTRACT_CONTEXT_STALE: reviewed_artifact_digest does not match bound_author_materialization_digest",
        "REVIEW_CONTRACT_CONTEXT_STALE: reviewed_program_digest does not match author_program_hash",
    ],
)
def test_classify_review_operation_maps_scope_mismatch_to_final_review_rewrite(proof_chain_error: str) -> None:
    operation = classify_review_operation(
        proof_chain_error=proof_chain_error,
        review_verdict=None,
        audit_error=None,
        preflight_blocked=False,
    )

    assert operation.operation == OP_FINAL_REVIEW_REWRITE_REQUIRED
    assert operation.blocking_reason_code == "REVIEW_SCOPE_MISMATCH"


def test_classify_review_operation_maps_format_invalid_to_final_review_rewrite() -> None:
    operation = classify_review_operation(
        proof_chain_error="FORBIDDEN_FINAL_REVIEW_NORMALIZATION: reviewed_artifact_paths must be a list",
        review_verdict=None,
        audit_error=None,
        preflight_blocked=False,
    )

    assert operation.operation == OP_FINAL_REVIEW_REWRITE_REQUIRED
    assert operation.blocking_reason_code == "REVIEW_FORMAT_INVALID"


def test_classify_review_operation_maps_audit_error_to_reviewer_restart() -> None:
    operation = classify_review_operation(
        proof_chain_error=None,
        review_verdict="PASS",
        audit_error="REVIEWER_WRITE_SCOPE_VIOLATION: reviewer wrote review/result/notes.yaml",
        preflight_blocked=False,
    )

    assert operation.operation == OP_REVIEWER_RESTART_REQUIRED
    assert operation.blocking_reason_code == "REVIEWER_SCOPE_VIOLATION"


def test_classify_review_operation_maps_generic_audit_error_to_audit_failed() -> None:
    operation = classify_review_operation(
        proof_chain_error=None,
        review_verdict="PASS",
        audit_error="reviewer_write_scope_audit.yaml review_cycle_id does not match reviewer_receipt.yaml",
        preflight_blocked=False,
    )

    assert operation.operation == OP_REVIEW_PREPARED
    assert operation.blocking_reason_code == "REVIEW_AUDIT_FAILED"


def test_classify_review_operation_prioritizes_audit_error_over_stale_proof_chain() -> None:
    operation = classify_review_operation(
        proof_chain_error="REVIEW_CONTRACT_CONTEXT_STALE: author digest changed after review request",
        review_verdict="PASS",
        audit_error="REVIEWER_WRITE_SCOPE_VIOLATION: reviewer wrote review/result/notes.yaml",
        preflight_blocked=False,
    )

    assert operation.operation == OP_REVIEWER_RESTART_REQUIRED
    assert operation.blocking_reason_code == "REVIEWER_SCOPE_VIOLATION"


def test_classify_review_operation_prioritizes_stale_proof_chain_over_generic_audit_error() -> None:
    operation = classify_review_operation(
        proof_chain_error=(
            "author/formal outputs or provenance changed after adversarial_review_request.yaml was issued; "
            "review cycle is stale"
        ),
        review_verdict="PASS",
        audit_error="reviewer_write_scope_audit.yaml review_cycle_id does not match reviewer_receipt.yaml",
        preflight_blocked=False,
    )

    assert operation.operation == OP_REQUEST_REFRESH_REQUIRED
    assert operation.blocking_reason_code == "AUTHOR_OUTPUTS_STALE"


def test_classify_review_operation_maps_preflight_block_to_author_fix_before_review() -> None:
    operation = classify_review_operation(
        proof_chain_error=None,
        review_verdict=None,
        audit_error=None,
        preflight_blocked=True,
    )

    assert operation.operation == OP_AUTHOR_FIX_REQUIRED_BEFORE_REVIEW
    assert operation.blocking_reason_code == "OUTPUTS_INVALID"


def test_classify_review_operation_maps_pass_for_retry_to_failure_handling() -> None:
    operation = classify_review_operation(
        proof_chain_error=None,
        review_verdict="PASS FOR RETRY",
        audit_error=None,
        preflight_blocked=False,
    )

    assert operation.operation == OP_FAILURE_HANDLING_REQUIRED
    assert operation.blocking_reason_code == "FAILURE_HANDLING_REQUIRED"


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


def test_map_review_ready_preflight_payload_blocks_request_refresh_for_stale_context() -> None:
    result = map_review_ready_preflight_payload(
        {
            "status": "FAIL",
            "content_findings": ["REVIEW_CONTRACT_CONTEXT_STALE: author digest drifted after prepare"],
            "upstream_binding_findings": [],
            "research_preflight_findings": [],
        }
    )

    assert result.status == REVIEW_READY_REQUEST_REFRESH_REQUIRED
    assert result.blocking_reason_code == "AUTHOR_OUTPUTS_STALE"
