from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

import yaml


ADVERSARIAL_REVIEW_REQUEST_FILENAME = "adversarial_review_request.yaml"
ADVERSARIAL_REVIEW_RESULT_FILENAME = "adversarial_review_result.yaml"
REVIEW_FINDINGS_FILENAME = "review_findings.yaml"
REQUIRED_REVIEWER_MODE = "adversarial"
FIX_REQUIRED_OUTCOME = "FIX_REQUIRED"
CLOSURE_READY_OUTCOMES = {
    "CLOSURE_READY_PASS": "PASS",
    "CLOSURE_READY_CONDITIONAL_PASS": "CONDITIONAL PASS",
    "CLOSURE_READY_PASS_FOR_RETRY": "PASS FOR RETRY",
    "CLOSURE_READY_RETRY": "RETRY",
    "CLOSURE_READY_NO_GO": "NO-GO",
    "CLOSURE_READY_CHILD_LINEAGE": "CHILD LINEAGE",
}
ALLOWED_REVIEW_LOOP_OUTCOMES = {FIX_REQUIRED_OUTCOME, *CLOSURE_READY_OUTCOMES}


@dataclass(frozen=True)
class ReviewerRuntimeIdentity:
    reviewer_identity: str
    reviewer_role: str
    reviewer_session_id: str
    reviewer_mode: str


def _require_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must load to a mapping")
    return payload


def _require_string(payload: dict[str, Any], key: str, *, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: {key} must be a non-empty string")
    return value.strip()


def _require_string_list(payload: dict[str, Any], key: str, *, path: Path) -> list[str]:
    value = payload.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{path}: {key} must be a list of non-empty strings")
    return [item.strip() for item in value]


def build_review_cycle_id(
    *,
    lineage_id: str,
    stage: str,
    author_identity: str,
    author_session_id: str,
    program_hash: str | None,
    stage_invoked_at: str | None,
    required_program_dir: str,
    required_program_entrypoint: str,
) -> str:
    digest = hashlib.sha256()
    for item in (
        lineage_id,
        stage,
        author_identity,
        author_session_id,
        program_hash or "",
        stage_invoked_at or "",
        required_program_dir,
        required_program_entrypoint,
    ):
        digest.update(item.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:16]


def ensure_adversarial_review_request(
    stage_dir: Path,
    *,
    lineage_id: str,
    stage: str,
    author_identity: str,
    author_session_id: str,
    required_program_dir: str,
    required_program_entrypoint: str,
    required_artifact_paths: list[str],
    required_provenance_paths: list[str],
    program_hash: str | None = None,
    stage_invoked_at: str | None = None,
) -> dict[str, Any]:
    request_path = stage_dir / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    review_cycle_id = build_review_cycle_id(
        lineage_id=lineage_id,
        stage=stage,
        author_identity=author_identity,
        author_session_id=author_session_id,
        program_hash=program_hash,
        stage_invoked_at=stage_invoked_at,
        required_program_dir=required_program_dir,
        required_program_entrypoint=required_program_entrypoint,
    )
    payload: dict[str, Any] = {
        "review_cycle_id": review_cycle_id,
        "lineage_id": lineage_id,
        "stage": stage,
        "author_identity": author_identity,
        "author_session_id": author_session_id,
        "required_program_dir": required_program_dir,
        "required_program_entrypoint": required_program_entrypoint,
        "required_artifact_paths": sorted(required_artifact_paths),
        "required_provenance_paths": sorted(required_provenance_paths),
        "required_reviewer_mode": REQUIRED_REVIEWER_MODE,
    }
    if program_hash:
        payload["author_program_hash"] = program_hash
    if stage_invoked_at:
        payload["author_stage_invoked_at"] = stage_invoked_at

    existing = load_adversarial_review_request(request_path) if request_path.exists() else None
    if existing is not None:
        assigned_identity = existing.get("assigned_reviewer_identity")
        assigned_session_id = existing.get("assigned_reviewer_session_id")
        if isinstance(assigned_identity, str) and assigned_identity.strip():
            payload["assigned_reviewer_identity"] = assigned_identity.strip()
        if isinstance(assigned_session_id, str) and assigned_session_id.strip():
            payload["assigned_reviewer_session_id"] = assigned_session_id.strip()
        if existing == payload:
            return existing

    request_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return payload


def load_adversarial_review_request(path: str | Path) -> dict[str, Any]:
    request_path = Path(path)
    payload = _require_mapping(request_path)
    data = {
        "review_cycle_id": _require_string(payload, "review_cycle_id", path=request_path),
        "lineage_id": _require_string(payload, "lineage_id", path=request_path),
        "stage": _require_string(payload, "stage", path=request_path),
        "author_identity": _require_string(payload, "author_identity", path=request_path),
        "author_session_id": _require_string(payload, "author_session_id", path=request_path),
        "required_program_dir": _require_string(payload, "required_program_dir", path=request_path),
        "required_program_entrypoint": _require_string(payload, "required_program_entrypoint", path=request_path),
        "required_artifact_paths": _require_string_list(payload, "required_artifact_paths", path=request_path),
        "required_provenance_paths": _require_string_list(payload, "required_provenance_paths", path=request_path),
        "required_reviewer_mode": _require_string(payload, "required_reviewer_mode", path=request_path),
    }
    if data["required_reviewer_mode"] != REQUIRED_REVIEWER_MODE:
        raise ValueError(
            f"{request_path}: required_reviewer_mode must be {REQUIRED_REVIEWER_MODE!r}"
        )
    for optional_key in (
        "author_program_hash",
        "author_stage_invoked_at",
        "assigned_reviewer_identity",
        "assigned_reviewer_session_id",
    ):
        value = payload.get(optional_key)
        if isinstance(value, str) and value.strip():
            data[optional_key] = value.strip()
    return data


def assign_runtime_reviewer_to_request(
    request_path: str | Path,
    request_payload: dict[str, Any],
    runtime_identity: ReviewerRuntimeIdentity,
) -> dict[str, Any]:
    assigned_identity = request_payload.get("assigned_reviewer_identity")
    assigned_session = request_payload.get("assigned_reviewer_session_id")
    if assigned_identity and assigned_identity != runtime_identity.reviewer_identity:
        raise ValueError(
            f"{request_path}: assigned reviewer {assigned_identity!r} does not match runtime reviewer "
            f"{runtime_identity.reviewer_identity!r}"
        )
    if assigned_session and assigned_session != runtime_identity.reviewer_session_id:
        raise ValueError(
            f"{request_path}: assigned reviewer session {assigned_session!r} does not match runtime session "
            f"{runtime_identity.reviewer_session_id!r}"
        )
    if (
        assigned_identity == runtime_identity.reviewer_identity
        and assigned_session == runtime_identity.reviewer_session_id
    ):
        return request_payload

    updated = dict(request_payload)
    updated["assigned_reviewer_identity"] = runtime_identity.reviewer_identity
    updated["assigned_reviewer_session_id"] = runtime_identity.reviewer_session_id
    Path(request_path).write_text(
        yaml.safe_dump(updated, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return updated


def load_adversarial_review_result(path: str | Path) -> dict[str, Any]:
    result_path = Path(path)
    payload = _require_mapping(result_path)
    outcome = _require_string(payload, "review_loop_outcome", path=result_path)
    if outcome not in ALLOWED_REVIEW_LOOP_OUTCOMES:
        raise ValueError(f"{result_path}: unsupported review_loop_outcome {outcome!r}")

    data = {
        "review_cycle_id": _require_string(payload, "review_cycle_id", path=result_path),
        "reviewer_identity": _require_string(payload, "reviewer_identity", path=result_path),
        "reviewer_role": _require_string(payload, "reviewer_role", path=result_path),
        "reviewer_session_id": _require_string(payload, "reviewer_session_id", path=result_path),
        "reviewer_mode": _require_string(payload, "reviewer_mode", path=result_path),
        "review_loop_outcome": outcome,
        "reviewed_program_dir": _require_string(payload, "reviewed_program_dir", path=result_path),
        "reviewed_program_entrypoint": _require_string(payload, "reviewed_program_entrypoint", path=result_path),
        "reviewed_artifact_paths": _require_string_list(payload, "reviewed_artifact_paths", path=result_path),
        "reviewed_provenance_paths": _require_string_list(payload, "reviewed_provenance_paths", path=result_path),
    }
    for key in (
        "blocking_findings",
        "reservation_findings",
        "info_findings",
        "residual_risks",
        "allowed_modifications",
        "downstream_permissions",
    ):
        data[key] = _require_string_list(payload, key, path=result_path)
    rollback_stage = payload.get("rollback_stage")
    if rollback_stage is not None:
        if not isinstance(rollback_stage, str) or not rollback_stage.strip():
            raise ValueError(f"{result_path}: rollback_stage must be a non-empty string when provided")
        data["rollback_stage"] = rollback_stage.strip()
    summary = payload.get("review_summary")
    if isinstance(summary, str) and summary.strip():
        data["review_summary"] = summary.strip()
    return data


def resolve_closure_verdict(review_loop_outcome: str) -> str | None:
    if review_loop_outcome == FIX_REQUIRED_OUTCOME:
        return None
    return CLOSURE_READY_OUTCOMES[review_loop_outcome]


def validate_result_against_request(
    *,
    request_payload: dict[str, Any],
    result_payload: dict[str, Any],
    runtime_identity: ReviewerRuntimeIdentity,
) -> None:
    if result_payload["review_cycle_id"] != request_payload["review_cycle_id"]:
        raise ValueError("adversarial_review_result.yaml review_cycle_id does not match the active request")
    if runtime_identity.reviewer_identity != result_payload["reviewer_identity"]:
        raise ValueError("runtime reviewer identity does not match adversarial_review_result.yaml")
    if runtime_identity.reviewer_role != result_payload["reviewer_role"]:
        raise ValueError("runtime reviewer role does not match adversarial_review_result.yaml")
    if runtime_identity.reviewer_session_id != result_payload["reviewer_session_id"]:
        raise ValueError("runtime reviewer session does not match adversarial_review_result.yaml")
    if runtime_identity.reviewer_mode != result_payload["reviewer_mode"]:
        raise ValueError("runtime reviewer mode does not match adversarial_review_result.yaml")
    if runtime_identity.reviewer_mode != request_payload["required_reviewer_mode"]:
        raise ValueError("runtime reviewer mode does not satisfy adversarial_review_request.yaml")
    assigned_identity = request_payload.get("assigned_reviewer_identity")
    assigned_session = request_payload.get("assigned_reviewer_session_id")
    if assigned_identity and assigned_identity != runtime_identity.reviewer_identity:
        raise ValueError("runtime reviewer identity does not match the reviewer assigned in adversarial_review_request.yaml")
    if assigned_session and assigned_session != runtime_identity.reviewer_session_id:
        raise ValueError("runtime reviewer session does not match the reviewer assigned in adversarial_review_request.yaml")
    if runtime_identity.reviewer_identity == request_payload["author_identity"]:
        raise ValueError("reviewer identity must differ from the author identity")
    if result_payload["reviewed_program_dir"] != request_payload["required_program_dir"]:
        raise ValueError("adversarial_review_result.yaml reviewed_program_dir does not match required_program_dir")
    if result_payload["reviewed_program_entrypoint"] != request_payload["required_program_entrypoint"]:
        raise ValueError(
            "adversarial_review_result.yaml reviewed_program_entrypoint does not match required_program_entrypoint"
        )
    if sorted(result_payload["reviewed_artifact_paths"]) != sorted(request_payload["required_artifact_paths"]):
        raise ValueError("adversarial_review_result.yaml reviewed_artifact_paths do not cover the required artifacts")
    if sorted(result_payload["reviewed_provenance_paths"]) != sorted(request_payload["required_provenance_paths"]):
        raise ValueError(
            "adversarial_review_result.yaml reviewed_provenance_paths do not cover the required provenance files"
        )
