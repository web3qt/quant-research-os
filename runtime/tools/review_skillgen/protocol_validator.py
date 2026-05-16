from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    FINAL_REVIEW_FILENAME,
    FIX_REQUIRED_OUTCOME,
    REQUIRED_REVIEWER_CONTEXT_SOURCE,
    REQUIRED_REVIEWER_HISTORY_INHERITANCE,
    REVIEWER_EXECUTION_MODE_SESSION,
    REVIEWER_RECEIPT_FILENAME,
    load_final_review,
    validate_receipt_against_request,
    validate_result_against_request,
)
from runtime.tools.review_skillgen.review_scope_builder import (
    stage_content_artifact_paths_from_request,
    stage_content_provenance_paths_from_request,
)
from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    REVIEWER_WRITE_SCOPE_AUDIT_FILENAME,
    load_reviewer_write_scope_audit,
    run_reviewer_write_scope_audit,
    validate_reviewer_write_scope_audit,
)
from runtime.tools.review_skillgen.review_result_writer import ensure_runtime_review_result


_FINAL_REVIEW_OUTCOME_BY_VERDICT = {
    "PASS": "CLOSURE_READY_PASS",
    "CONDITIONAL PASS": "CLOSURE_READY_CONDITIONAL_PASS",
    "FIX_REQUIRED": FIX_REQUIRED_OUTCOME,
    "RETRY": "CLOSURE_READY_RETRY",
    "NO-GO": "CLOSURE_READY_NO_GO",
    "CHILD LINEAGE": "CLOSURE_READY_CHILD_LINEAGE",
}


def _project_final_review_result(
    *,
    request_payload: dict[str, Any],
    runtime_identity: Any,
    final_review_payload: dict[str, Any],
) -> dict[str, Any]:
    if final_review_payload["lineage_id"] != request_payload["lineage_id"]:
        raise ValueError("review/final_review.yaml lineage_id does not match the active request")
    if final_review_payload["stage_id"] != request_payload["stage"]:
        raise ValueError("review/final_review.yaml stage_id does not match the active request")
    if final_review_payload["reviewer_identity"] != runtime_identity.reviewer_identity:
        raise ValueError("runtime reviewer identity does not match review/final_review.yaml")
    if runtime_identity.reviewer_mode != request_payload["required_reviewer_mode"]:
        raise ValueError("runtime reviewer mode does not satisfy adversarial_review_request.yaml")
    if runtime_identity.reviewer_identity == request_payload["author_identity"]:
        raise ValueError("reviewer identity must differ from the author identity")

    expected_program_path = (
        f"{request_payload['required_program_dir']}/{request_payload['required_program_entrypoint']}"
    )
    if final_review_payload["reviewed_program_path"] != expected_program_path:
        raise ValueError("review/final_review.yaml reviewed_program_path does not match the active request")

    expected_artifact_paths = stage_content_artifact_paths_from_request(request_payload)
    if sorted(final_review_payload["reviewed_artifact_paths"]) != expected_artifact_paths:
        raise ValueError("review/final_review.yaml reviewed_artifact_paths do not match the active request")

    review_result = {
        "review_cycle_id": request_payload["review_cycle_id"],
        "reviewer_identity": final_review_payload["reviewer_identity"],
        "reviewer_role": runtime_identity.reviewer_role,
        "reviewer_session_id": runtime_identity.reviewer_session_id,
        "reviewer_mode": runtime_identity.reviewer_mode,
        "reviewer_agent_id": final_review_payload["reviewer_agent_id"],
        "reviewer_execution_mode": REVIEWER_EXECUTION_MODE_SESSION,
        "reviewer_context_source": REQUIRED_REVIEWER_CONTEXT_SOURCE,
        "reviewer_history_inheritance": REQUIRED_REVIEWER_HISTORY_INHERITANCE,
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "review_loop_outcome": _FINAL_REVIEW_OUTCOME_BY_VERDICT[final_review_payload["verdict"]],
        "reviewed_program_dir": request_payload["required_program_dir"],
        "reviewed_program_entrypoint": request_payload["required_program_entrypoint"],
        "reviewed_artifact_paths": expected_artifact_paths,
        "reviewed_provenance_paths": stage_content_provenance_paths_from_request(request_payload),
        "reviewed_project_root": request_payload["project_root"],
        "reviewed_lineage_root": request_payload["lineage_root"],
        "reviewed_stage_dir": request_payload["stage_dir"],
        "hard_gate_findings_acknowledged": True,
        "blocking_findings": list(final_review_payload["blocking_findings"]),
        "reservation_findings": list(final_review_payload["reservation_findings"]),
        "info_findings": list(final_review_payload["info_findings"]),
        "residual_risks": list(final_review_payload["residual_risks"]),
        "allowed_modifications": list(final_review_payload["allowed_modifications"]),
        "downstream_permissions": list(final_review_payload["downstream_permissions"]),
        "review_summary": final_review_payload["review_summary"],
    }
    rollback_stage = final_review_payload.get("rollback_stage")
    if isinstance(rollback_stage, str) and rollback_stage.strip():
        review_result["rollback_stage"] = rollback_stage.strip()
    return review_result


def load_and_validate_protocol(
    *,
    review_request_dir: Path,
    review_result_dir: Path,
    request_loader: Any,
    receipt_loader: Any,
    runtime_identity: Any,
) -> dict[str, Any]:
    request_path = review_request_dir / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    receipt_path = review_request_dir / REVIEWER_RECEIPT_FILENAME
    result_path = review_result_dir / ADVERSARIAL_REVIEW_RESULT_FILENAME
    audit_path = review_result_dir / REVIEWER_WRITE_SCOPE_AUDIT_FILENAME
    stage_dir = review_request_dir.parent.parent

    request_payload = request_loader(request_path)
    final_review_path = stage_dir / "review" / FINAL_REVIEW_FILENAME
    if final_review_path.exists():
        final_review_payload = load_final_review(final_review_path)
        review_result = _project_final_review_result(
            request_payload=request_payload,
            runtime_identity=runtime_identity,
            final_review_payload=final_review_payload,
        )
        return {
            "request_payload": request_payload,
            "receipt_payload": {},
            "review_result": review_result,
            "audit_payload": {},
        }

    receipt_payload = receipt_loader(receipt_path)
    validate_receipt_against_request(
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        runtime_identity=runtime_identity,
    )

    raw_path = review_result_dir / "reviewer_findings.raw.yaml"
    if result_path.exists() and not raw_path.exists():
        raise ValueError(
            "REVIEW_RESULT_PROJECTION_DRIFT: PROTECTED_STATE_DRIFT: "
            "reviewer_findings.raw.yaml is required for active-cycle review closure"
        )

    review_result = ensure_runtime_review_result(
        review_result_dir=review_result_dir,
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        runtime_identity=runtime_identity,
    )
    validate_result_against_request(
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        result_payload=review_result,
        runtime_identity=runtime_identity,
    )

    if (
        not audit_path.exists()
        or audit_path.stat().st_mtime < result_path.stat().st_mtime
        or audit_path.stat().st_mtime < receipt_path.stat().st_mtime
    ):
        audit_payload = run_reviewer_write_scope_audit(stage_dir)
    else:
        audit_payload = load_reviewer_write_scope_audit(audit_path)
    validate_reviewer_write_scope_audit(
        receipt_payload=receipt_payload,
        audit_payload=audit_payload,
        stage_dir=stage_dir,
    )

    return {
        "request_payload": request_payload,
        "receipt_payload": receipt_payload,
        "review_result": review_result,
        "audit_payload": audit_payload,
    }
