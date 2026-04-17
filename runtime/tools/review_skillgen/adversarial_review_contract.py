from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

import yaml


ADVERSARIAL_REVIEW_REQUEST_FILENAME = "adversarial_review_request.yaml"
ADVERSARIAL_REVIEW_RESULT_FILENAME = "adversarial_review_result.yaml"
SPAWNED_REVIEWER_RECEIPT_FILENAME = "spawned_reviewer_receipt.yaml"
SPAWNED_REVIEWER_HANDOFF_MANIFEST_FILENAME = "spawned_reviewer_handoff_manifest.yaml"
REVIEW_FINDINGS_FILENAME = "review_findings.yaml"
REQUIRED_REVIEWER_MODE = "adversarial"
REQUIRED_REVIEWER_EXECUTION_MODE = "spawned_agent"
REQUIRED_REVIEWER_CONTEXT_SOURCE = "explicit_handoff_only"
REQUIRED_REVIEWER_HISTORY_INHERITANCE = "none"
REQUIRED_RESULT_WRITE_ROOT = "review/result"
RUNTIME_LAUNCHER_OWNER = "qros-runtime-launcher"
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
REQUIRED_HANDOFF_INPUT_ROOTS = ("review/request", "author/formal")


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


def _require_bool(payload: dict[str, Any], key: str, *, path: Path) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{path}: {key} must be a boolean")
    return value


def _require_string_list(payload: dict[str, Any], key: str, *, path: Path) -> list[str]:
    value = payload.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{path}: {key} must be a list of non-empty strings")
    return [item.strip() for item in value]


def _stable_yaml_text(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(payload, sort_keys=True, allow_unicode=True)


def _digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stage_dir_from_request_path(request_path: Path) -> Path:
    return request_path.parents[2]


def _handoff_manifest_path_for_stage(stage_dir: Path) -> Path:
    return stage_dir / "review" / "request" / SPAWNED_REVIEWER_HANDOFF_MANIFEST_FILENAME


def _receipt_path_for_stage(stage_dir: Path) -> Path:
    return stage_dir / "review" / "request" / SPAWNED_REVIEWER_RECEIPT_FILENAME


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


def _build_handoff_manifest_payload(
    *,
    review_cycle_id: str,
    lineage_id: str,
    stage: str,
    required_program_dir: str,
    required_program_entrypoint: str,
    required_artifact_paths: list[str],
    required_provenance_paths: list[str],
) -> dict[str, Any]:
    return {
        "review_cycle_id": review_cycle_id,
        "lineage_id": lineage_id,
        "stage": stage,
        "required_program_dir": required_program_dir,
        "required_program_entrypoint": required_program_entrypoint,
        "required_artifact_paths": sorted(required_artifact_paths),
        "required_provenance_paths": sorted(required_provenance_paths),
        "permitted_input_roots": list(REQUIRED_HANDOFF_INPUT_ROOTS),
        "permitted_output_roots": [REQUIRED_RESULT_WRITE_ROOT],
        "required_result_write_root": REQUIRED_RESULT_WRITE_ROOT,
    }


def _write_handoff_manifest(
    stage_dir: Path,
    *,
    review_cycle_id: str,
    lineage_id: str,
    stage: str,
    required_program_dir: str,
    required_program_entrypoint: str,
    required_artifact_paths: list[str],
    required_provenance_paths: list[str],
) -> tuple[str, str]:
    manifest_path = _handoff_manifest_path_for_stage(stage_dir)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _build_handoff_manifest_payload(
        review_cycle_id=review_cycle_id,
        lineage_id=lineage_id,
        stage=stage,
        required_program_dir=required_program_dir,
        required_program_entrypoint=required_program_entrypoint,
        required_artifact_paths=required_artifact_paths,
        required_provenance_paths=required_provenance_paths,
    )
    manifest_text = _stable_yaml_text(payload)
    if not manifest_path.exists() or manifest_path.read_text(encoding="utf-8") != manifest_text:
        manifest_path.write_text(manifest_text, encoding="utf-8")
    return (
        str(manifest_path.relative_to(stage_dir)),
        _digest_text(manifest_text),
    )


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
    request_path = stage_dir / "review" / "request" / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    request_path.parent.mkdir(parents=True, exist_ok=True)
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
    handoff_manifest_path, handoff_manifest_digest = _write_handoff_manifest(
        stage_dir,
        review_cycle_id=review_cycle_id,
        lineage_id=lineage_id,
        stage=stage,
        required_program_dir=required_program_dir,
        required_program_entrypoint=required_program_entrypoint,
        required_artifact_paths=required_artifact_paths,
        required_provenance_paths=required_provenance_paths,
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
        "handoff_manifest_path": handoff_manifest_path,
        "handoff_manifest_digest": handoff_manifest_digest,
        "required_result_write_root": REQUIRED_RESULT_WRITE_ROOT,
    }
    if program_hash:
        payload["author_program_hash"] = program_hash
    if stage_invoked_at:
        payload["author_stage_invoked_at"] = stage_invoked_at

    existing = load_adversarial_review_request(request_path) if request_path.exists() else None
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
        "handoff_manifest_path": _require_string(payload, "handoff_manifest_path", path=request_path),
        "handoff_manifest_digest": _require_string(payload, "handoff_manifest_digest", path=request_path),
        "required_result_write_root": _require_string(payload, "required_result_write_root", path=request_path),
    }
    if data["required_reviewer_mode"] != REQUIRED_REVIEWER_MODE:
        raise ValueError(f"{request_path}: required_reviewer_mode must be {REQUIRED_REVIEWER_MODE!r}")
    if data["required_result_write_root"] != REQUIRED_RESULT_WRITE_ROOT:
        raise ValueError(
            f"{request_path}: required_result_write_root must be {REQUIRED_RESULT_WRITE_ROOT!r}"
        )
    for optional_key in ("author_program_hash", "author_stage_invoked_at"):
        value = payload.get(optional_key)
        if isinstance(value, str) and value.strip():
            data[optional_key] = value.strip()

    stage_dir = _stage_dir_from_request_path(request_path)
    manifest_path = stage_dir / data["handoff_manifest_path"]
    if not manifest_path.exists():
        raise ValueError(f"{request_path}: handoff manifest {data['handoff_manifest_path']!r} is missing")
    manifest_text = manifest_path.read_text(encoding="utf-8")
    if _digest_text(manifest_text) != data["handoff_manifest_digest"]:
        raise ValueError(f"{request_path}: handoff manifest digest does not match {manifest_path}")
    return data


def issue_spawned_reviewer_receipt(
    stage_dir: Path,
    *,
    reviewer_identity: str,
    reviewer_session_id: str,
    launcher_session_id: str,
    launcher_owner: str = RUNTIME_LAUNCHER_OWNER,
) -> dict[str, Any]:
    request_path = stage_dir / "review" / "request" / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    request_payload = load_adversarial_review_request(request_path)
    receipt_path = _receipt_path_for_stage(stage_dir)
    payload = {
        "review_cycle_id": request_payload["review_cycle_id"],
        "launcher_owner": launcher_owner,
        "launcher_session_id": launcher_session_id,
        "spawn_mode": REQUIRED_REVIEWER_EXECUTION_MODE,
        "fork_context": False,
        "write_root": REQUIRED_RESULT_WRITE_ROOT,
        "handoff_manifest_path": request_payload["handoff_manifest_path"],
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "requested_reviewer_identity": reviewer_identity,
        "requested_reviewer_session_id": reviewer_session_id,
        "receipt_written_at": datetime.now(timezone.utc).isoformat(),
    }
    if receipt_path.exists():
        existing = load_spawned_reviewer_receipt(receipt_path)
        if {**payload, "receipt_written_at": existing["receipt_written_at"]} == existing:
            return existing
    receipt_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return payload


def load_spawned_reviewer_receipt(path: str | Path) -> dict[str, Any]:
    receipt_path = Path(path)
    if not receipt_path.exists():
        raise ValueError(f"{receipt_path}: {SPAWNED_REVIEWER_RECEIPT_FILENAME} is missing")
    payload = _require_mapping(receipt_path)
    data = {
        "review_cycle_id": _require_string(payload, "review_cycle_id", path=receipt_path),
        "launcher_owner": _require_string(payload, "launcher_owner", path=receipt_path),
        "launcher_session_id": _require_string(payload, "launcher_session_id", path=receipt_path),
        "spawn_mode": _require_string(payload, "spawn_mode", path=receipt_path),
        "fork_context": _require_bool(payload, "fork_context", path=receipt_path),
        "write_root": _require_string(payload, "write_root", path=receipt_path),
        "handoff_manifest_path": _require_string(payload, "handoff_manifest_path", path=receipt_path),
        "handoff_manifest_digest": _require_string(payload, "handoff_manifest_digest", path=receipt_path),
        "requested_reviewer_identity": _require_string(payload, "requested_reviewer_identity", path=receipt_path),
        "requested_reviewer_session_id": _require_string(payload, "requested_reviewer_session_id", path=receipt_path),
        "receipt_written_at": _require_string(payload, "receipt_written_at", path=receipt_path),
    }
    return data


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
        "reviewer_execution_mode": _require_string(payload, "reviewer_execution_mode", path=result_path),
        "reviewer_context_source": _require_string(payload, "reviewer_context_source", path=result_path),
        "reviewer_history_inheritance": _require_string(payload, "reviewer_history_inheritance", path=result_path),
        "handoff_manifest_digest": _require_string(payload, "handoff_manifest_digest", path=result_path),
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
    for timestamp_key in ("review_started_at", "review_completed_at"):
        value = payload.get(timestamp_key)
        if isinstance(value, str) and value.strip():
            data[timestamp_key] = value.strip()
    return data


def canonicalize_runtime_review_result(
    result_path: str | Path,
    *,
    request_payload: dict[str, Any],
    result_payload: dict[str, Any],
) -> dict[str, Any]:
    canonical: dict[str, Any] = {
        "review_cycle_id": result_payload["review_cycle_id"],
        "reviewer_identity": result_payload["reviewer_identity"],
        "reviewer_role": result_payload["reviewer_role"],
        "reviewer_session_id": result_payload["reviewer_session_id"],
        "reviewer_mode": result_payload["reviewer_mode"],
        "reviewer_execution_mode": result_payload["reviewer_execution_mode"],
        "reviewer_context_source": result_payload["reviewer_context_source"],
        "reviewer_history_inheritance": result_payload["reviewer_history_inheritance"],
        "handoff_manifest_digest": result_payload["handoff_manifest_digest"],
        "review_loop_outcome": result_payload["review_loop_outcome"],
        "reviewed_program_dir": request_payload["required_program_dir"],
        "reviewed_program_entrypoint": request_payload["required_program_entrypoint"],
        "reviewed_artifact_paths": sorted(request_payload["required_artifact_paths"]),
        "reviewed_provenance_paths": sorted(request_payload["required_provenance_paths"]),
        "blocking_findings": list(result_payload["blocking_findings"]),
        "reservation_findings": list(result_payload["reservation_findings"]),
        "info_findings": list(result_payload["info_findings"]),
        "residual_risks": list(result_payload["residual_risks"]),
        "allowed_modifications": list(result_payload["allowed_modifications"]),
        "downstream_permissions": list(result_payload["downstream_permissions"]),
    }
    for key in ("rollback_stage", "review_summary", "review_started_at", "review_completed_at"):
        value = result_payload.get(key)
        if value is not None:
            canonical[key] = value

    if canonical != result_payload:
        Path(result_path).write_text(
            yaml.safe_dump(canonical, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return canonical


def resolve_closure_verdict(review_loop_outcome: str) -> str | None:
    if review_loop_outcome == FIX_REQUIRED_OUTCOME:
        return None
    return CLOSURE_READY_OUTCOMES[review_loop_outcome]


def validate_receipt_against_request(
    *,
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
    runtime_identity: ReviewerRuntimeIdentity,
) -> None:
    validate_receipt_contract(
        request_payload=request_payload,
        receipt_payload=receipt_payload,
    )
    if receipt_payload["requested_reviewer_identity"] != runtime_identity.reviewer_identity:
        raise ValueError("runtime reviewer identity does not match spawned_reviewer_receipt.yaml")
    if receipt_payload["requested_reviewer_session_id"] != runtime_identity.reviewer_session_id:
        raise ValueError("runtime reviewer session does not match spawned_reviewer_receipt.yaml")


def validate_receipt_contract(
    *,
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
) -> None:
    if receipt_payload["review_cycle_id"] != request_payload["review_cycle_id"]:
        raise ValueError("spawned_reviewer_receipt.yaml review_cycle_id does not match the active request")
    if receipt_payload["launcher_owner"] != RUNTIME_LAUNCHER_OWNER:
        raise ValueError("spawned_reviewer_receipt.yaml launcher_owner is not the fixed runtime launcher")
    if receipt_payload["spawn_mode"] != REQUIRED_REVIEWER_EXECUTION_MODE:
        raise ValueError("spawned_reviewer_receipt.yaml spawn_mode must be spawned_agent")
    if receipt_payload["fork_context"] is not False:
        raise ValueError("spawned_reviewer_receipt.yaml fork_context must be false")
    if receipt_payload["write_root"] != request_payload["required_result_write_root"]:
        raise ValueError("spawned_reviewer_receipt.yaml write_root does not match the active request")
    if receipt_payload["handoff_manifest_path"] != request_payload["handoff_manifest_path"]:
        raise ValueError("spawned_reviewer_receipt.yaml handoff_manifest_path does not match the active request")
    if receipt_payload["handoff_manifest_digest"] != request_payload["handoff_manifest_digest"]:
        raise ValueError("spawned_reviewer_receipt.yaml handoff_manifest_digest does not match the active request")


def validate_result_against_request(
    *,
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
    result_payload: dict[str, Any],
    runtime_identity: ReviewerRuntimeIdentity,
) -> None:
    validate_result_contract(
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        result_payload=result_payload,
    )
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


def validate_result_contract(
    *,
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
    result_payload: dict[str, Any],
) -> None:
    if result_payload["review_cycle_id"] != request_payload["review_cycle_id"]:
        raise ValueError("adversarial_review_result.yaml review_cycle_id does not match the active request")
    if receipt_payload["requested_reviewer_identity"] != result_payload["reviewer_identity"]:
        raise ValueError("adversarial_review_result.yaml reviewer_identity does not match spawned_reviewer_receipt.yaml")
    if receipt_payload["requested_reviewer_session_id"] != result_payload["reviewer_session_id"]:
        raise ValueError("adversarial_review_result.yaml reviewer_session_id does not match spawned_reviewer_receipt.yaml")
    if result_payload["reviewer_execution_mode"] != REQUIRED_REVIEWER_EXECUTION_MODE:
        raise ValueError("adversarial_review_result.yaml reviewer_execution_mode must be spawned_agent")
    if result_payload["reviewer_context_source"] != REQUIRED_REVIEWER_CONTEXT_SOURCE:
        raise ValueError("adversarial_review_result.yaml reviewer_context_source must be explicit_handoff_only")
    if result_payload["reviewer_history_inheritance"] != REQUIRED_REVIEWER_HISTORY_INHERITANCE:
        raise ValueError("adversarial_review_result.yaml reviewer_history_inheritance must be none")
    if result_payload["handoff_manifest_digest"] != request_payload["handoff_manifest_digest"]:
        raise ValueError("adversarial_review_result.yaml handoff_manifest_digest does not match the active request")
    if result_payload["handoff_manifest_digest"] != receipt_payload["handoff_manifest_digest"]:
        raise ValueError("adversarial_review_result.yaml handoff_manifest_digest does not match spawned_reviewer_receipt.yaml")
