from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    FIX_REQUIRED_OUTCOME,
    ReviewerRuntimeIdentity,
    canonicalize_runtime_review_result,
    load_adversarial_review_result,
    resolve_closure_verdict,
)
from runtime.tools.review_skillgen.review_scope_builder import (
    stage_content_artifact_paths_from_request,
    stage_content_provenance_paths_from_request,
)


RAW_REVIEWER_FINDINGS_FILENAME = "reviewer_findings.raw.yaml"


def _load_raw_reviewer_findings(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: raw reviewer findings must load to a mapping")
    outcome = payload.get("review_loop_outcome")
    if not isinstance(outcome, str) or not outcome.strip():
        raise ValueError(f"{path}: review_loop_outcome must be a non-empty string")
    return {
        "review_loop_outcome": outcome.strip(),
        "blocking_findings": [str(item) for item in payload.get("blocking_findings", []) or []],
        "reservation_findings": [str(item) for item in payload.get("reservation_findings", []) or []],
        "info_findings": [str(item) for item in payload.get("info_findings", []) or []],
        "residual_risks": [str(item) for item in payload.get("residual_risks", []) or []],
        "allowed_modifications": [str(item) for item in payload.get("allowed_modifications", []) or []],
        "downstream_permissions": [str(item) for item in payload.get("downstream_permissions", []) or []],
        "rollback_stage": payload.get("rollback_stage"),
        "review_summary": payload.get("review_summary"),
    }


def _review_findings_payload(
    *,
    reviewer_identity: str,
    review_loop_outcome: str,
    raw_payload: dict[str, Any],
) -> dict[str, Any]:
    recommended_verdict = "RETRY" if review_loop_outcome == FIX_REQUIRED_OUTCOME else resolve_closure_verdict(review_loop_outcome)
    return {
        "reviewer_identity": reviewer_identity,
        "recommended_verdict": recommended_verdict,
        "blocking_findings": list(raw_payload["blocking_findings"]),
        "reservation_findings": list(raw_payload["reservation_findings"]),
        "info_findings": list(raw_payload["info_findings"]),
        "residual_risks": list(raw_payload["residual_risks"]),
        "allowed_modifications": list(raw_payload["allowed_modifications"]),
        "downstream_permissions": list(raw_payload["downstream_permissions"]),
        "rollback_stage": raw_payload.get("rollback_stage"),
    }


def ensure_runtime_review_result(
    *,
    review_result_dir: Path,
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
    runtime_identity: ReviewerRuntimeIdentity,
) -> dict[str, Any]:
    result_path = review_result_dir / ADVERSARIAL_REVIEW_RESULT_FILENAME
    if result_path.exists():
        existing = load_adversarial_review_result(result_path)
        return canonicalize_runtime_review_result(
            result_path,
            request_payload=request_payload,
            result_payload=existing,
        )

    raw_path = review_result_dir / RAW_REVIEWER_FINDINGS_FILENAME
    if not raw_path.exists():
        raise ValueError(f"{result_path}: adversarial_review_result.yaml is missing")

    raw_payload = _load_raw_reviewer_findings(raw_path)
    result_payload: dict[str, Any] = {
        "review_cycle_id": request_payload["review_cycle_id"],
        "reviewer_identity": runtime_identity.reviewer_identity,
        "reviewer_role": runtime_identity.reviewer_role,
        "reviewer_session_id": runtime_identity.reviewer_session_id,
        "reviewer_mode": runtime_identity.reviewer_mode,
        "reviewer_agent_id": receipt_payload["spawned_agent_id"],
        "reviewer_execution_mode": "spawned_agent",
        "reviewer_context_source": "explicit_handoff_only",
        "reviewer_history_inheritance": "none",
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "review_loop_outcome": raw_payload["review_loop_outcome"],
        "reviewed_program_dir": request_payload["required_program_dir"],
        "reviewed_program_entrypoint": request_payload["required_program_entrypoint"],
        "reviewed_artifact_paths": stage_content_artifact_paths_from_request(request_payload),
        "reviewed_provenance_paths": stage_content_provenance_paths_from_request(request_payload),
        "blocking_findings": list(raw_payload["blocking_findings"]),
        "reservation_findings": list(raw_payload["reservation_findings"]),
        "info_findings": list(raw_payload["info_findings"]),
        "residual_risks": list(raw_payload["residual_risks"]),
        "allowed_modifications": list(raw_payload["allowed_modifications"]),
        "downstream_permissions": list(raw_payload["downstream_permissions"]),
    }
    for key in ("rollback_stage", "review_summary"):
        value = raw_payload.get(key)
        if isinstance(value, str) and value.strip():
            result_payload[key] = value.strip()

    result_path.write_text(
        yaml.safe_dump(result_payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    review_findings_path = review_result_dir / "review_findings.yaml"
    if not review_findings_path.exists():
        review_findings_path.write_text(
            yaml.safe_dump(
                _review_findings_payload(
                    reviewer_identity=runtime_identity.reviewer_identity,
                    review_loop_outcome=raw_payload["review_loop_outcome"],
                    raw_payload=raw_payload,
                ),
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )

    return load_adversarial_review_result(result_path)
