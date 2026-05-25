from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    FINAL_REVIEW_FILENAME,
    FIX_REQUIRED_OUTCOME,
    REVIEWER_RECEIPT_FILENAME,
    RUNTIME_LAUNCHER_OWNER,
    validate_receipt_against_request,
    validate_result_against_request,
)
from runtime.tools.review_skillgen.final_review_normalizer import (
    normalize_final_review_payload,
    validate_final_review_digest_bindings,
    write_normalized_final_review,
)
from runtime.tools.review_skillgen.review_scope_builder import (
    stage_content_provenance_paths_from_request,
)
from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    REVIEWER_WRITE_SCOPE_AUDIT_FILENAME,
    load_reviewer_write_scope_audit,
    run_reviewer_write_scope_audit,
    validate_reviewer_write_scope_audit,
)
from runtime.tools.review_skillgen.review_result_writer import ensure_runtime_review_result
from runtime.tools.review_skillgen.review_runtime_state import compute_author_materialization_digest_fresh
from runtime.tools.stage_evaluator import STAGE_EVALUATOR_SPECS


_FINAL_REVIEW_OUTCOME_BY_VERDICT = {
    "PASS": "CLOSURE_READY_PASS",
    "CONDITIONAL PASS": "CLOSURE_READY_CONDITIONAL_PASS",
    "FIX_REQUIRED": FIX_REQUIRED_OUTCOME,
    "RETRY": "CLOSURE_READY_RETRY",
    "NO-GO": "CLOSURE_READY_NO_GO",
    "CHILD LINEAGE": "CLOSURE_READY_CHILD_LINEAGE",
}


def _current_required_outputs_truth(request_payload: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    spec = STAGE_EVALUATOR_SPECS.get(request_payload["stage"])
    if spec is None:
        return tuple(request_payload["required_artifact_paths"]), tuple(request_payload["required_provenance_paths"])
    return tuple(spec.required_outputs), ("program_execution_manifest.json",)


def _validate_bound_author_digest(request_payload: dict[str, Any], review_request_dir: Path) -> None:
    bound_author_digest = request_payload.get("bound_author_materialization_digest")
    if not isinstance(bound_author_digest, str) or not bound_author_digest.strip():
        raise ValueError(
            "REVIEW_CONTRACT_CONTEXT_STALE: active request is missing "
            "bound_author_materialization_digest; rerun qros-review-cycle prepare"
        )

    current_required_outputs, current_required_provenance_paths = _current_required_outputs_truth(request_payload)
    current_author_digest = compute_author_materialization_digest_fresh(
        artifact_root=review_request_dir.parent.parent / "author" / "formal",
        required_outputs=current_required_outputs,
        required_provenance_paths=current_required_provenance_paths,
    )
    if current_author_digest != bound_author_digest:
        raise ValueError("REVIEW_CONTRACT_CONTEXT_STALE: author digest drifted after prepare")


def _validate_stage_contract_context(request_payload: dict[str, Any], review_request_dir: Path) -> None:
    _validate_bound_author_digest(request_payload, review_request_dir)

    context_relpath = request_payload.get("stage_contract_context_yaml_path")
    if not isinstance(context_relpath, str) or not context_relpath.strip():
        raise ValueError(
            "REVIEW_CONTRACT_CONTEXT_STALE: active request is missing stage_contract_context_yaml_path; "
            "rerun qros-review-cycle prepare"
        )

    context_path = review_request_dir.parent.parent / context_relpath
    if not context_path.exists():
        raise ValueError("REVIEW_CONTRACT_CONTEXT_STALE: stage contract context file is missing")

    context_text = context_path.read_text(encoding="utf-8")
    context_payload = yaml.safe_load(context_text)
    if not isinstance(context_payload, dict):
        raise ValueError("REVIEW_CONTRACT_CONTEXT_STALE: stage contract context must be a mapping")
    if context_payload.get("review_cycle_id") != request_payload["review_cycle_id"]:
        raise ValueError("REVIEW_CONTRACT_CONTEXT_STALE: review_cycle_id does not match the active request")

    bound_author_digest = request_payload.get("bound_author_materialization_digest")
    if isinstance(bound_author_digest, str) and bound_author_digest.strip():
        if context_payload.get("author_materialization_digest") != bound_author_digest:
            raise ValueError("REVIEW_CONTRACT_CONTEXT_STALE: author digest does not match the active request")

    expected_digest = request_payload.get("stage_contract_context_digest")
    if isinstance(expected_digest, str) and expected_digest.strip():
        current_digest = hashlib.sha256(context_text.encode("utf-8")).hexdigest()
        if current_digest != expected_digest:
            raise ValueError("REVIEW_CONTRACT_CONTEXT_STALE: stage contract context digest changed after prepare")


def _project_final_review_result(
    *,
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
    runtime_identity: Any,
    normalized_final_review: dict[str, Any],
) -> dict[str, Any]:
    if runtime_identity.reviewer_mode != request_payload["required_reviewer_mode"]:
        raise ValueError("runtime reviewer mode does not satisfy adversarial_review_request.yaml")
    if runtime_identity.reviewer_identity == request_payload["author_identity"]:
        raise ValueError("reviewer identity must differ from the author identity")

    review_result = {
        "review_cycle_id": request_payload["review_cycle_id"],
        "reviewer_identity": receipt_payload["requested_reviewer_identity"],
        "reviewer_role": runtime_identity.reviewer_role,
        "reviewer_session_id": receipt_payload["requested_reviewer_session_id"],
        "reviewer_mode": runtime_identity.reviewer_mode,
        "reviewer_agent_id": receipt_payload["reviewer_agent_id"],
        "reviewer_execution_mode": receipt_payload["execution_mode"],
        "reviewer_context_source": receipt_payload["reviewer_context_source"],
        "reviewer_history_inheritance": receipt_payload["reviewer_history_inheritance"],
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "review_loop_outcome": _FINAL_REVIEW_OUTCOME_BY_VERDICT[normalized_final_review["verdict"]],
        "reviewed_program_dir": request_payload["required_program_dir"],
        "reviewed_program_entrypoint": request_payload["required_program_entrypoint"],
        "reviewed_artifact_paths": list(normalized_final_review["reviewed_artifact_paths"]),
        "reviewed_provenance_paths": stage_content_provenance_paths_from_request(request_payload),
        "reviewed_project_root": request_payload["project_root"],
        "reviewed_lineage_root": request_payload["lineage_root"],
        "reviewed_stage_dir": request_payload["stage_dir"],
        "hard_gate_findings_acknowledged": True,
        "blocking_findings": list(normalized_final_review["blocking_findings"]),
        "reservation_findings": list(normalized_final_review["reservation_findings"]),
        "info_findings": list(normalized_final_review["info_findings"]),
        "residual_risks": list(normalized_final_review["residual_risks"]),
        "allowed_modifications": list(normalized_final_review["allowed_modifications"]),
        "downstream_permissions": list(normalized_final_review["downstream_permissions"]),
        "review_summary": normalized_final_review["review_summary"],
    }
    rollback_stage = normalized_final_review.get("rollback_stage")
    if isinstance(rollback_stage, str) and rollback_stage.strip():
        review_result["rollback_stage"] = rollback_stage.strip()
    return review_result


def _validate_final_review_reviewer_is_bound_reviewer(receipt_payload: dict[str, Any]) -> None:
    if receipt_payload["requested_reviewer_identity"] == RUNTIME_LAUNCHER_OWNER:
        raise ValueError("REVIEWER_UNBOUND: launcher identity cannot be reviewer for final review")


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
        if not receipt_path.exists():
            raise ValueError("REVIEWER_UNBOUND: review/final_review.yaml exists without active reviewer_receipt.yaml")

        _validate_stage_contract_context(request_payload, review_request_dir)
        receipt_payload = receipt_loader(receipt_path)
        validate_receipt_against_request(
            request_payload=request_payload,
            receipt_payload=receipt_payload,
            runtime_identity=runtime_identity,
        )
        _validate_final_review_reviewer_is_bound_reviewer(receipt_payload)

        raw_payload = yaml.safe_load(final_review_path.read_text(encoding="utf-8"))
        if not isinstance(raw_payload, dict):
            raise ValueError("review/final_review.yaml must load to a mapping")
        normalized_final_review = normalize_final_review_payload(
            final_review_payload=raw_payload,
            request_payload=request_payload,
            receipt_payload=receipt_payload,
        )
        validate_final_review_digest_bindings(
            normalized_final_review=normalized_final_review,
            request_payload=request_payload,
        )
        write_normalized_final_review(
            stage_dir=stage_dir,
            final_review_payload=raw_payload,
            request_payload=request_payload,
            receipt_payload=receipt_payload,
        )
        review_result = _project_final_review_result(
            request_payload=request_payload,
            receipt_payload=receipt_payload,
            runtime_identity=runtime_identity,
            normalized_final_review=normalized_final_review,
        )
        validate_result_against_request(
            request_payload=request_payload,
            receipt_payload=receipt_payload,
            result_payload=review_result,
            runtime_identity=runtime_identity,
        )
        return {
            "request_payload": request_payload,
            "receipt_payload": receipt_payload,
            "review_result": review_result,
            "audit_payload": {},
        }

    _validate_stage_contract_context(request_payload, review_request_dir)
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
