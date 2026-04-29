from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    ALLOWED_REVIEW_LOOP_OUTCOMES,
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


def _allowed_review_loop_outcomes_message() -> str:
    return ", ".join(sorted(ALLOWED_REVIEW_LOOP_OUTCOMES))


def _require_raw_string_list(payload: dict[str, Any], key: str, *, path: Path) -> list[str]:
    value = payload.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{path}: {key} must be a list of strings when provided")
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{path}: {key} must be a list of strings when provided")
    return [item for item in value]


def _load_raw_reviewer_findings(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: raw reviewer findings must load to a mapping")
    outcome = payload.get("review_loop_outcome")
    if not isinstance(outcome, str) or not outcome.strip():
        raise ValueError(f"{path}: review_loop_outcome must be a non-empty string")
    outcome = outcome.strip()
    if outcome not in ALLOWED_REVIEW_LOOP_OUTCOMES:
        raise ValueError(
            f"{path}: unsupported raw review_loop_outcome {outcome!r}; "
            f"allowed values: {_allowed_review_loop_outcomes_message()}"
        )
    return {
        "review_loop_outcome": outcome,
        "blocking_findings": _require_raw_string_list(payload, "blocking_findings", path=path),
        "reservation_findings": _require_raw_string_list(payload, "reservation_findings", path=path),
        "info_findings": _require_raw_string_list(payload, "info_findings", path=path),
        "residual_risks": _require_raw_string_list(payload, "residual_risks", path=path),
        "allowed_modifications": _require_raw_string_list(payload, "allowed_modifications", path=path),
        "downstream_permissions": _require_raw_string_list(payload, "downstream_permissions", path=path),
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
    raw_path = review_result_dir / RAW_REVIEWER_FINDINGS_FILENAME
    if raw_path.exists():
        raw_payload = _load_raw_reviewer_findings(raw_path)
        result_payload: dict[str, Any] = {
            "review_cycle_id": request_payload["review_cycle_id"],
            "reviewer_identity": runtime_identity.reviewer_identity,
            "reviewer_role": runtime_identity.reviewer_role,
            "reviewer_session_id": runtime_identity.reviewer_session_id,
            "reviewer_mode": runtime_identity.reviewer_mode,
            "reviewer_agent_id": receipt_payload["spawned_agent_id"],
            "reviewer_execution_mode": receipt_payload["spawn_mode"],
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
        raw_path.unlink()
        return load_adversarial_review_result(result_path)

    if result_path.exists():
        existing = load_adversarial_review_result(result_path)
        return canonicalize_runtime_review_result(
            result_path,
            request_payload=request_payload,
            result_payload=existing,
        )

    raise ValueError(f"{result_path}: adversarial_review_result.yaml is missing")
