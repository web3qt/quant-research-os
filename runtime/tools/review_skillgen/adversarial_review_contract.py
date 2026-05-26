from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

import yaml
from runtime.tools.review_skillgen.review_cycle_trace import append_review_cycle_event
from runtime.tools.review_skillgen.review_scope_builder import build_review_scope
from runtime.tools.review_skillgen.review_scope_builder import (
    stage_content_artifact_paths_from_request,
    stage_content_provenance_paths_from_request,
)


ADVERSARIAL_REVIEW_REQUEST_FILENAME = "adversarial_review_request.yaml"
ADVERSARIAL_REVIEW_RESULT_FILENAME = "adversarial_review_result.yaml"
FINAL_REVIEW_FILENAME = "final_review.yaml"
REVIEWER_RECEIPT_FILENAME = "reviewer_receipt.yaml"
REVIEWER_HANDOFF_MANIFEST_FILENAME = "reviewer_handoff_manifest.yaml"
REVIEW_FINDINGS_FILENAME = "review_findings.yaml"
REQUIRED_REVIEWER_MODE = "adversarial"
REVIEWER_EXECUTION_MODE_SPAWNED = "spawned_agent"
REVIEWER_EXECUTION_MODE_SESSION = "review_session"
REVIEW_CONTEXT_ROOT_MISMATCH = "REVIEW_CONTEXT_ROOT_MISMATCH"
ALLOWED_REVIEWER_EXECUTION_MODES = {
    REVIEWER_EXECUTION_MODE_SPAWNED,
    REVIEWER_EXECUTION_MODE_SESSION,
}
REQUIRED_REVIEWER_CONTEXT_SOURCE = "explicit_handoff_only"
REQUIRED_REVIEWER_HISTORY_INHERITANCE = "none"
REQUIRED_RESULT_WRITE_ROOT = "review/result"
REQUIRED_REVIEWER_WRITE_PATH = f"review/{FINAL_REVIEW_FILENAME}"
RUNTIME_LAUNCHER_OWNER = "qros-runtime-launcher"
REQUIRED_LAUNCHER_REVIEW_READY_STATUS = "complete"

ALLOWED_HOSTS = {"codex", "claude-code"}
REVIEWER_INVOCATION_KIND_CODEX_SPAWN = "codex_spawn_agent"
REVIEWER_INVOCATION_KIND_CLAUDE_PLUGIN = "claude_plugin_agent"
ALLOWED_REVIEWER_INVOCATION_KINDS = {
    REVIEWER_INVOCATION_KIND_CODEX_SPAWN,
    REVIEWER_INVOCATION_KIND_CLAUDE_PLUGIN,
}
CONTEXT_ISOLATION_FORK_FALSE = "fork_context_false"
CONTEXT_ISOLATION_SEPARATE_SUBAGENT = "separate_subagent_context"
ALLOWED_CONTEXT_ISOLATION_POLICIES = {
    CONTEXT_ISOLATION_FORK_FALSE,
    CONTEXT_ISOLATION_SEPARATE_SUBAGENT,
}
HANDOFF_DELIVERY_SEND_INPUT = "send_input"
HANDOFF_DELIVERY_AGENT_TASK = "agent_task_context"
ALLOWED_HANDOFF_DELIVERY_METHODS = {
    HANDOFF_DELIVERY_SEND_INPUT,
    HANDOFF_DELIVERY_AGENT_TASK,
}

HOST_REVIEWER_INVOCATION_KIND: dict[str, str] = {
    "codex": REVIEWER_INVOCATION_KIND_CODEX_SPAWN,
    "claude-code": REVIEWER_INVOCATION_KIND_CLAUDE_PLUGIN,
}
HOST_CONTEXT_ISOLATION: dict[str, str] = {
    "codex": CONTEXT_ISOLATION_FORK_FALSE,
    "claude-code": CONTEXT_ISOLATION_SEPARATE_SUBAGENT,
}
HOST_HANDOFF_DELIVERY: dict[str, str] = {
    "codex": HANDOFF_DELIVERY_SEND_INPUT,
    "claude-code": HANDOFF_DELIVERY_AGENT_TASK,
}
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
ALLOWED_FINAL_REVIEW_VERDICTS = {
    "PASS",
    "CONDITIONAL PASS",
    "FIX_REQUIRED",
    "RETRY",
    "NO-GO",
    "CHILD LINEAGE",
}
REQUIRED_HANDOFF_INPUT_ROOTS = ("review/request", "author/formal")
REQUIRED_HANDOFF_CONTEXT_PATHS = ("artifact_catalog.md", "field_dictionary.md", "run_manifest.json")
CANONICAL_REVIEW_CONTEXT_FIELDS = (
    "project_root",
    "lineage_root",
    "stage_dir",
    "author_formal_dir",
    "review_request_dir",
    "review_result_dir",
)
RECEIPT_CANONICAL_CONTEXT_FIELDS = ("project_root", "lineage_root", "stage_dir")
RECEIPT_ISOLATION_FIELDS = ("reviewer_context_source", "reviewer_history_inheritance")
RECEIPT_REQUIRED_FIELDS = RECEIPT_CANONICAL_CONTEXT_FIELDS + RECEIPT_ISOLATION_FIELDS


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


def _optional_string(payload: dict[str, Any], key: str, *, default: str) -> str:
    value = payload.get(key)
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        return default
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


def _require_non_empty_string_list(payload: dict[str, Any], key: str, *, path: Path) -> list[str]:
    values = _require_string_list(payload, key, path=path)
    if not values:
        raise ValueError(f"{path}: {key} must be a non-empty list of non-empty strings")
    return values


def _require_nullable_string(payload: dict[str, Any], key: str, *, path: Path) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: {key} must be a non-empty string when provided")
    return value.strip()


def _stable_yaml_text(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(payload, sort_keys=True, allow_unicode=True)


def _digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stage_dir_from_request_path(request_path: Path) -> Path:
    return request_path.parents[2]


def _canonical_review_context(stage_dir: Path) -> dict[str, str]:
    resolved_stage_dir = stage_dir.resolve()
    lineage_root = resolved_stage_dir.parent
    project_root = lineage_root.parent.parent
    return {
        "project_root": str(project_root),
        "lineage_root": str(lineage_root),
        "stage_dir": str(resolved_stage_dir),
        "author_formal_dir": str((resolved_stage_dir / "author" / "formal").resolve()),
        "review_request_dir": str((resolved_stage_dir / "review" / "request").resolve()),
        "review_result_dir": str((resolved_stage_dir / "review" / "result").resolve()),
    }


def _validated_canonical_review_context(
    payload: dict[str, Any],
    *,
    stage_dir: Path,
    path: Path,
) -> dict[str, str]:
    expected_context = _canonical_review_context(stage_dir)
    observed_context = {
        key: _require_string(payload, key, path=path)
        for key in CANONICAL_REVIEW_CONTEXT_FIELDS
    }
    for key, expected_value in expected_context.items():
        if observed_context[key] != expected_value:
            raise ValueError(f"{path}: {key} must match the canonical review context")
    return observed_context


def _handoff_manifest_path_for_stage(stage_dir: Path) -> Path:
    return stage_dir / "review" / "request" / REVIEWER_HANDOFF_MANIFEST_FILENAME


def _receipt_path_for_stage(stage_dir: Path) -> Path:
    return stage_dir / "review" / "request" / REVIEWER_RECEIPT_FILENAME


def _expected_launcher_handoff_context_paths(required_artifact_paths: list[str]) -> list[str]:
    required_set = set(required_artifact_paths)
    return [path for path in REQUIRED_HANDOFF_CONTEXT_PATHS if path in required_set]


def _build_launcher_review_ready_payload(
    *,
    required_artifact_paths: list[str],
    required_provenance_paths: list[str],
) -> dict[str, Any]:
    return {
        "launcher_review_ready_status": REQUIRED_LAUNCHER_REVIEW_READY_STATUS,
        "launcher_checked_artifact_paths": sorted(required_artifact_paths),
        "launcher_checked_provenance_paths": sorted(required_provenance_paths),
        "launcher_handoff_context_paths": _expected_launcher_handoff_context_paths(required_artifact_paths),
    }


def _validate_review_ready_stage_inputs(
    stage_dir: Path,
    *,
    required_artifact_paths: list[str],
    required_provenance_paths: list[str],
) -> None:
    author_formal_dir = stage_dir / "author" / "formal"
    for relative_path in sorted(required_artifact_paths):
        artifact_path = author_formal_dir / relative_path
        if not artifact_path.exists():
            raise ValueError(f"{stage_dir}: review-ready artifact {relative_path!r} is missing under author/formal")
        if artifact_path.is_file() and artifact_path.stat().st_size == 0:
            raise ValueError(f"{stage_dir}: review-ready artifact {relative_path!r} is empty under author/formal")
    for relative_path in sorted(required_provenance_paths):
        provenance_candidates = [stage_dir / relative_path, author_formal_dir / relative_path]
        provenance_path = next((candidate for candidate in provenance_candidates if candidate.exists()), None)
        if provenance_path is None:
            raise ValueError(f"{stage_dir}: review-ready provenance {relative_path!r} is missing")
        if provenance_path.is_file() and provenance_path.stat().st_size == 0:
            raise ValueError(f"{stage_dir}: review-ready provenance {relative_path!r} is empty")


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
    stage_dir: Path,
    review_cycle_id: str,
    lineage_id: str,
    stage: str,
    required_program_dir: str,
    required_program_entrypoint: str,
    required_artifact_paths: list[str],
    required_provenance_paths: list[str],
) -> dict[str, Any]:
    review_scope = build_review_scope(
        stage=stage,
        required_artifact_paths=required_artifact_paths,
        required_provenance_paths=required_provenance_paths,
    )
    payload = {
        "review_cycle_id": review_cycle_id,
        "lineage_id": lineage_id,
        "stage": stage,
        "required_program_dir": required_program_dir,
        "required_program_entrypoint": required_program_entrypoint,
        "required_artifact_paths": review_scope["required_artifact_paths"],
        "required_provenance_paths": review_scope["required_provenance_paths"],
        "stage_content_artifact_paths": review_scope["stage_content_artifact_paths"],
        "stage_content_provenance_paths": review_scope["stage_content_provenance_paths"],
        "upstream_binding_artifact_paths": review_scope["upstream_binding_artifact_paths"],
        "upstream_binding_provenance_paths": review_scope["upstream_binding_provenance_paths"],
        "permitted_input_roots": list(REQUIRED_HANDOFF_INPUT_ROOTS),
        "permitted_output_roots": [REQUIRED_REVIEWER_WRITE_PATH],
        "required_reviewer_write_path": REQUIRED_REVIEWER_WRITE_PATH,
        "required_result_write_root": REQUIRED_RESULT_WRITE_ROOT,
    }
    payload.update(_canonical_review_context(stage_dir))
    payload.update(
        _build_launcher_review_ready_payload(
            required_artifact_paths=required_artifact_paths,
            required_provenance_paths=required_provenance_paths,
        )
    )
    return payload


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
        stage_dir=stage_dir,
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
    _validate_review_ready_stage_inputs(
        stage_dir,
        required_artifact_paths=required_artifact_paths,
        required_provenance_paths=required_provenance_paths,
    )
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
    review_scope = build_review_scope(
        stage=stage,
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
        "required_artifact_paths": review_scope["required_artifact_paths"],
        "required_provenance_paths": review_scope["required_provenance_paths"],
        "stage_content_artifact_paths": review_scope["stage_content_artifact_paths"],
        "stage_content_provenance_paths": review_scope["stage_content_provenance_paths"],
        "upstream_binding_artifact_paths": review_scope["upstream_binding_artifact_paths"],
        "upstream_binding_provenance_paths": review_scope["upstream_binding_provenance_paths"],
        "required_reviewer_mode": REQUIRED_REVIEWER_MODE,
        "handoff_manifest_path": handoff_manifest_path,
        "handoff_manifest_digest": handoff_manifest_digest,
        "required_reviewer_write_path": REQUIRED_REVIEWER_WRITE_PATH,
        "required_result_write_root": REQUIRED_RESULT_WRITE_ROOT,
    }
    payload.update(_canonical_review_context(stage_dir))
    payload.update(
        _build_launcher_review_ready_payload(
            required_artifact_paths=required_artifact_paths,
            required_provenance_paths=required_provenance_paths,
        )
    )
    if program_hash:
        payload["author_program_hash"] = program_hash
    if stage_invoked_at:
        payload["author_stage_invoked_at"] = stage_invoked_at

    existing: dict[str, Any] | None = None
    raw_existing: dict[str, Any] | None = None
    if request_path.exists():
        try:
            raw_existing = _require_mapping(request_path)
        except Exception:
            raw_existing = None
        try:
            existing = load_adversarial_review_request(request_path)
        except Exception:
            if raw_existing is not None and (
                raw_existing.get("review_cycle_id") != payload["review_cycle_id"]
                or raw_existing.get("handoff_manifest_digest") != payload["handoff_manifest_digest"]
            ):
                request_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
            return payload
    if existing == payload:
        return existing

    request_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    append_review_cycle_event(
        stage_dir,
        event_type="request_issued",
        review_cycle_id=payload["review_cycle_id"],
        payload={
            "lineage_id": payload["lineage_id"],
            "stage": payload["stage"],
            "author_identity": payload["author_identity"],
            "author_session_id": payload["author_session_id"],
            "required_program_dir": payload["required_program_dir"],
            "required_program_entrypoint": payload["required_program_entrypoint"],
            "required_artifact_paths": list(payload["required_artifact_paths"]),
            "required_provenance_paths": list(payload["required_provenance_paths"]),
            "launcher_review_ready_status": payload["launcher_review_ready_status"],
            "launcher_handoff_context_paths": list(payload["launcher_handoff_context_paths"]),
            "handoff_manifest_digest": payload["handoff_manifest_digest"],
        },
    )
    return payload


def load_adversarial_review_request(path: str | Path) -> dict[str, Any]:
    request_path = Path(path)
    payload = _require_mapping(request_path)
    stage_dir = _stage_dir_from_request_path(request_path)
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
        "stage_content_artifact_paths": _require_string_list(payload, "stage_content_artifact_paths", path=request_path)
        if "stage_content_artifact_paths" in payload
        else [],
        "stage_content_provenance_paths": _require_string_list(
            payload, "stage_content_provenance_paths", path=request_path
        )
        if "stage_content_provenance_paths" in payload
        else [],
        "upstream_binding_artifact_paths": _require_string_list(
            payload, "upstream_binding_artifact_paths", path=request_path
        )
        if "upstream_binding_artifact_paths" in payload
        else [],
        "upstream_binding_provenance_paths": _require_string_list(
            payload, "upstream_binding_provenance_paths", path=request_path
        )
        if "upstream_binding_provenance_paths" in payload
        else [],
        "required_reviewer_mode": _require_string(payload, "required_reviewer_mode", path=request_path),
        "handoff_manifest_path": _require_string(payload, "handoff_manifest_path", path=request_path),
        "handoff_manifest_digest": _require_string(payload, "handoff_manifest_digest", path=request_path),
        "required_reviewer_write_path": _optional_string(
            payload,
            "required_reviewer_write_path",
            default=REQUIRED_REVIEWER_WRITE_PATH,
        ),
        "required_result_write_root": _require_string(payload, "required_result_write_root", path=request_path),
        "launcher_review_ready_status": _require_string(payload, "launcher_review_ready_status", path=request_path),
        "launcher_checked_artifact_paths": _require_string_list(
            payload, "launcher_checked_artifact_paths", path=request_path
        ),
        "launcher_checked_provenance_paths": _require_string_list(
            payload, "launcher_checked_provenance_paths", path=request_path
        ),
        "launcher_handoff_context_paths": _require_string_list(
            payload, "launcher_handoff_context_paths", path=request_path
        ),
    }
    data.update(_validated_canonical_review_context(payload, stage_dir=stage_dir, path=request_path))
    if data["required_reviewer_mode"] != REQUIRED_REVIEWER_MODE:
        raise ValueError(f"{request_path}: required_reviewer_mode must be {REQUIRED_REVIEWER_MODE!r}")
    if data["required_reviewer_write_path"] != REQUIRED_REVIEWER_WRITE_PATH:
        raise ValueError(
            f"{request_path}: required_reviewer_write_path must be {REQUIRED_REVIEWER_WRITE_PATH!r}"
        )
    if data["required_result_write_root"] != REQUIRED_RESULT_WRITE_ROOT:
        raise ValueError(
            f"{request_path}: required_result_write_root must be {REQUIRED_RESULT_WRITE_ROOT!r}"
        )
    if data["launcher_review_ready_status"] != REQUIRED_LAUNCHER_REVIEW_READY_STATUS:
        raise ValueError(
            f"{request_path}: launcher_review_ready_status must be {REQUIRED_LAUNCHER_REVIEW_READY_STATUS!r}"
        )
    if sorted(data["launcher_checked_artifact_paths"]) != sorted(data["required_artifact_paths"]):
        raise ValueError(f"{request_path}: launcher_checked_artifact_paths must match required_artifact_paths")
    if sorted(data["launcher_checked_provenance_paths"]) != sorted(data["required_provenance_paths"]):
        raise ValueError(f"{request_path}: launcher_checked_provenance_paths must match required_provenance_paths")
    expected_scope = build_review_scope(
        stage=data["stage"],
        required_artifact_paths=data["required_artifact_paths"],
        required_provenance_paths=data["required_provenance_paths"],
    )
    for scope_key in (
        "stage_content_artifact_paths",
        "stage_content_provenance_paths",
        "upstream_binding_artifact_paths",
        "upstream_binding_provenance_paths",
    ):
        expected = expected_scope[scope_key]
        observed = sorted(data.get(scope_key, []))
        if observed and observed != sorted(expected):
            raise ValueError(f"{request_path}: {scope_key} do not match the expected stage review scope")
        data[scope_key] = sorted(expected)
    expected_context_paths = _expected_launcher_handoff_context_paths(data["required_artifact_paths"])
    if sorted(data["launcher_handoff_context_paths"]) != sorted(expected_context_paths):
        raise ValueError(f"{request_path}: launcher_handoff_context_paths do not match the required handoff context")
    for optional_key in ("author_program_hash", "author_stage_invoked_at"):
        value = payload.get(optional_key)
        if isinstance(value, str) and value.strip():
            data[optional_key] = value.strip()
    for optional_key in (
        "bound_author_materialization_digest",
        "stage_contract_context_yaml_path",
        "stage_contract_context_md_path",
        "stage_contract_context_digest",
    ):
        value = payload.get(optional_key)
        if isinstance(value, str) and value.strip():
            data[optional_key] = value.strip()

    manifest_path = stage_dir / data["handoff_manifest_path"]
    if not manifest_path.exists():
        raise ValueError(f"{request_path}: handoff manifest {data['handoff_manifest_path']!r} is missing")
    manifest_text = manifest_path.read_text(encoding="utf-8")
    if _digest_text(manifest_text) != data["handoff_manifest_digest"]:
        raise ValueError(f"{request_path}: handoff manifest digest does not match {manifest_path}")
    manifest_payload = load_reviewer_handoff_manifest(manifest_path)
    for key in (
        "review_cycle_id",
        "lineage_id",
        "stage",
        "required_program_dir",
        "required_program_entrypoint",
        "required_artifact_paths",
        "required_provenance_paths",
        "stage_content_artifact_paths",
        "stage_content_provenance_paths",
        "upstream_binding_artifact_paths",
        "upstream_binding_provenance_paths",
        "required_result_write_root",
        "launcher_review_ready_status",
        "launcher_checked_artifact_paths",
        "launcher_checked_provenance_paths",
        "launcher_handoff_context_paths",
        *CANONICAL_REVIEW_CONTEXT_FIELDS,
    ):
        if manifest_payload[key] != data[key]:
            raise ValueError(f"{request_path}: handoff manifest field {key} does not match the active request")
    return data


def load_reviewer_handoff_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    payload = _require_mapping(manifest_path)
    stage_dir = _stage_dir_from_request_path(manifest_path)
    data = {
        "review_cycle_id": _require_string(payload, "review_cycle_id", path=manifest_path),
        "lineage_id": _require_string(payload, "lineage_id", path=manifest_path),
        "stage": _require_string(payload, "stage", path=manifest_path),
        "required_program_dir": _require_string(payload, "required_program_dir", path=manifest_path),
        "required_program_entrypoint": _require_string(payload, "required_program_entrypoint", path=manifest_path),
        "required_artifact_paths": _require_string_list(payload, "required_artifact_paths", path=manifest_path),
        "required_provenance_paths": _require_string_list(payload, "required_provenance_paths", path=manifest_path),
        "stage_content_artifact_paths": _require_string_list(
            payload, "stage_content_artifact_paths", path=manifest_path
        )
        if "stage_content_artifact_paths" in payload
        else [],
        "stage_content_provenance_paths": _require_string_list(
            payload, "stage_content_provenance_paths", path=manifest_path
        )
        if "stage_content_provenance_paths" in payload
        else [],
        "upstream_binding_artifact_paths": _require_string_list(
            payload, "upstream_binding_artifact_paths", path=manifest_path
        )
        if "upstream_binding_artifact_paths" in payload
        else [],
        "upstream_binding_provenance_paths": _require_string_list(
            payload, "upstream_binding_provenance_paths", path=manifest_path
        )
        if "upstream_binding_provenance_paths" in payload
        else [],
        "permitted_input_roots": _require_string_list(payload, "permitted_input_roots", path=manifest_path),
        "permitted_output_roots": _require_string_list(payload, "permitted_output_roots", path=manifest_path),
        "required_reviewer_write_path": _optional_string(
            payload,
            "required_reviewer_write_path",
            default=REQUIRED_REVIEWER_WRITE_PATH,
        ),
        "required_result_write_root": _require_string(payload, "required_result_write_root", path=manifest_path),
        "launcher_review_ready_status": _require_string(payload, "launcher_review_ready_status", path=manifest_path),
        "launcher_checked_artifact_paths": _require_string_list(
            payload, "launcher_checked_artifact_paths", path=manifest_path
        ),
        "launcher_checked_provenance_paths": _require_string_list(
            payload, "launcher_checked_provenance_paths", path=manifest_path
        ),
        "launcher_handoff_context_paths": _require_string_list(
            payload, "launcher_handoff_context_paths", path=manifest_path
        ),
    }
    data.update(_validated_canonical_review_context(payload, stage_dir=stage_dir, path=manifest_path))
    if tuple(data["permitted_input_roots"]) != REQUIRED_HANDOFF_INPUT_ROOTS:
        raise ValueError(f"{manifest_path}: permitted_input_roots must be {list(REQUIRED_HANDOFF_INPUT_ROOTS)!r}")
    if data["permitted_output_roots"] != [REQUIRED_REVIEWER_WRITE_PATH]:
        raise ValueError(f"{manifest_path}: permitted_output_roots must be {[REQUIRED_REVIEWER_WRITE_PATH]!r}")
    if data["required_reviewer_write_path"] != REQUIRED_REVIEWER_WRITE_PATH:
        raise ValueError(
            f"{manifest_path}: required_reviewer_write_path must be {REQUIRED_REVIEWER_WRITE_PATH!r}"
        )
    if data["required_result_write_root"] != REQUIRED_RESULT_WRITE_ROOT:
        raise ValueError(f"{manifest_path}: required_result_write_root must be {REQUIRED_RESULT_WRITE_ROOT!r}")
    if data["launcher_review_ready_status"] != REQUIRED_LAUNCHER_REVIEW_READY_STATUS:
        raise ValueError(
            f"{manifest_path}: launcher_review_ready_status must be {REQUIRED_LAUNCHER_REVIEW_READY_STATUS!r}"
        )
    if sorted(data["launcher_checked_artifact_paths"]) != sorted(data["required_artifact_paths"]):
        raise ValueError(f"{manifest_path}: launcher_checked_artifact_paths must match required_artifact_paths")
    if sorted(data["launcher_checked_provenance_paths"]) != sorted(data["required_provenance_paths"]):
        raise ValueError(f"{manifest_path}: launcher_checked_provenance_paths must match required_provenance_paths")
    expected_scope = build_review_scope(
        stage=data["stage"],
        required_artifact_paths=data["required_artifact_paths"],
        required_provenance_paths=data["required_provenance_paths"],
    )
    for scope_key in (
        "stage_content_artifact_paths",
        "stage_content_provenance_paths",
        "upstream_binding_artifact_paths",
        "upstream_binding_provenance_paths",
    ):
        expected = expected_scope[scope_key]
        observed = sorted(data.get(scope_key, []))
        if observed and observed != sorted(expected):
            raise ValueError(f"{manifest_path}: {scope_key} do not match the expected stage review scope")
        data[scope_key] = sorted(expected)
    expected_context_paths = _expected_launcher_handoff_context_paths(data["required_artifact_paths"])
    if sorted(data["launcher_handoff_context_paths"]) != sorted(expected_context_paths):
        raise ValueError(f"{manifest_path}: launcher_handoff_context_paths do not match the required handoff context")
    return data


def issue_reviewer_receipt(
    stage_dir: Path,
    *,
    reviewer_identity: str,
    reviewer_session_id: str,
    launcher_session_id: str,
    launcher_thread_id: str,
    reviewer_agent_id: str,
    execution_mode: str = REVIEWER_EXECUTION_MODE_SPAWNED,
    host: str = "codex",
    launcher_owner: str = RUNTIME_LAUNCHER_OWNER,
) -> dict[str, Any]:
    from runtime.tools.review_skillgen.reviewer_write_scope_audit import write_reviewer_write_scope_baseline

    if host not in ALLOWED_HOSTS:
        raise ValueError(f"unsupported host: {host!r}")

    request_path = stage_dir / "review" / "request" / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    request_payload = load_adversarial_review_request(request_path)
    receipt_path = _receipt_path_for_stage(stage_dir)
    payload = {
        "review_cycle_id": request_payload["review_cycle_id"],
        "project_root": request_payload["project_root"],
        "lineage_root": request_payload["lineage_root"],
        "stage_dir": request_payload["stage_dir"],
        "host": host,
        "launcher_owner": launcher_owner,
        "launcher_session_id": launcher_session_id,
        "launcher_thread_id": launcher_thread_id,
        "execution_mode": execution_mode,
        "reviewer_invocation_kind": HOST_REVIEWER_INVOCATION_KIND[host],
        "context_isolation_policy": HOST_CONTEXT_ISOLATION[host],
        "handoff_delivery_method": HOST_HANDOFF_DELIVERY[host],
        "reviewer_agent_id": reviewer_agent_id,
        "write_root": REQUIRED_REVIEWER_WRITE_PATH,
        "reviewer_owned_write_path": REQUIRED_REVIEWER_WRITE_PATH,
        "handoff_manifest_path": request_payload["handoff_manifest_path"],
        "handoff_manifest_digest": request_payload["handoff_manifest_digest"],
        "requested_reviewer_identity": reviewer_identity,
        "requested_reviewer_session_id": reviewer_session_id,
        "receipt_written_at": datetime.now(timezone.utc).isoformat(),
        "reviewer_context_source": REQUIRED_REVIEWER_CONTEXT_SOURCE,
        "reviewer_history_inheritance": REQUIRED_REVIEWER_HISTORY_INHERITANCE,
    }
    if receipt_path.exists():
        try:
            existing = load_reviewer_receipt(receipt_path)
        except ValueError:
            raw_existing = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
            if not isinstance(raw_existing, dict):
                raise
            existing_review_cycle_id = raw_existing.get("review_cycle_id")
            if existing_review_cycle_id is not None and existing_review_cycle_id != payload["review_cycle_id"]:
                raise
            missing_context_fields = [key for key in RECEIPT_REQUIRED_FIELDS if key not in raw_existing]
            for key in RECEIPT_REQUIRED_FIELDS:
                if key in raw_existing and raw_existing[key] != payload[key]:
                    raise
            if not missing_context_fields:
                raise
            candidate = dict(raw_existing)
            for key in missing_context_fields:
                candidate[key] = payload[key]
            receipt_written_at = candidate.get("receipt_written_at")
            if not isinstance(receipt_written_at, str) or not receipt_written_at.strip():
                raise
            if {**payload, "receipt_written_at": receipt_written_at} != candidate:
                raise
            # 旧 receipt 缺少 canonical context / isolation 字段；同一 review cycle 可刷新为当前合同形状。
        else:
            if existing["review_cycle_id"] != payload["review_cycle_id"]:
                raise ValueError("existing reviewer_receipt.yaml review_cycle_id does not match the active request")
            validate_receipt_contract(request_payload=request_payload, receipt_payload=existing)
            if {**payload, "receipt_written_at": existing["receipt_written_at"]} == existing:
                write_reviewer_write_scope_baseline(
                    stage_dir,
                    review_cycle_id=existing["review_cycle_id"],
                    launcher_thread_id=existing["launcher_thread_id"],
                    reviewer_agent_id=existing["reviewer_agent_id"],
                )
                return existing
    receipt_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    write_reviewer_write_scope_baseline(
        stage_dir,
        review_cycle_id=payload["review_cycle_id"],
        launcher_thread_id=payload["launcher_thread_id"],
        reviewer_agent_id=payload["reviewer_agent_id"],
    )
    append_review_cycle_event(
        stage_dir,
        event_type="receipt_issued",
        review_cycle_id=payload["review_cycle_id"],
        payload={
            "host": payload["host"],
            "launcher_session_id": payload["launcher_session_id"],
            "launcher_thread_id": payload["launcher_thread_id"],
            "requested_reviewer_identity": payload["requested_reviewer_identity"],
            "requested_reviewer_session_id": payload["requested_reviewer_session_id"],
            "reviewer_agent_id": payload["reviewer_agent_id"],
            "execution_mode": payload["execution_mode"],
            "context_isolation_policy": payload["context_isolation_policy"],
            "reviewer_context_source": payload["reviewer_context_source"],
            "reviewer_history_inheritance": payload["reviewer_history_inheritance"],
            "write_root": payload["write_root"],
            "handoff_manifest_digest": payload["handoff_manifest_digest"],
        },
    )
    return payload


def load_reviewer_receipt(path: str | Path) -> dict[str, Any]:
    receipt_path = Path(path)
    if not receipt_path.exists():
        raise ValueError(f"{receipt_path}: {REVIEWER_RECEIPT_FILENAME} is missing")
    payload = _require_mapping(receipt_path)
    data = {
        "review_cycle_id": _require_string(payload, "review_cycle_id", path=receipt_path),
        "project_root": _require_string(payload, "project_root", path=receipt_path),
        "lineage_root": _require_string(payload, "lineage_root", path=receipt_path),
        "stage_dir": _require_string(payload, "stage_dir", path=receipt_path),
        "host": _require_string(payload, "host", path=receipt_path),
        "launcher_owner": _require_string(payload, "launcher_owner", path=receipt_path),
        "launcher_session_id": _require_string(payload, "launcher_session_id", path=receipt_path),
        "launcher_thread_id": _require_string(payload, "launcher_thread_id", path=receipt_path),
        "execution_mode": _require_string(payload, "execution_mode", path=receipt_path),
        "reviewer_invocation_kind": _require_string(payload, "reviewer_invocation_kind", path=receipt_path),
        "context_isolation_policy": _require_string(payload, "context_isolation_policy", path=receipt_path),
        "handoff_delivery_method": _require_string(payload, "handoff_delivery_method", path=receipt_path),
        "reviewer_agent_id": _require_string(payload, "reviewer_agent_id", path=receipt_path),
        "write_root": _require_string(payload, "write_root", path=receipt_path),
        "handoff_manifest_path": _require_string(payload, "handoff_manifest_path", path=receipt_path),
        "handoff_manifest_digest": _require_string(payload, "handoff_manifest_digest", path=receipt_path),
        "requested_reviewer_identity": _require_string(payload, "requested_reviewer_identity", path=receipt_path),
        "requested_reviewer_session_id": _require_string(payload, "requested_reviewer_session_id", path=receipt_path),
        "receipt_written_at": _require_string(payload, "receipt_written_at", path=receipt_path),
        "reviewer_context_source": _require_string(payload, "reviewer_context_source", path=receipt_path),
        "reviewer_history_inheritance": _require_string(payload, "reviewer_history_inheritance", path=receipt_path),
    }
    if data["host"] not in ALLOWED_HOSTS:
        raise ValueError(f"{receipt_path}: host must be one of {sorted(ALLOWED_HOSTS)!r}")
    if data["execution_mode"] not in ALLOWED_REVIEWER_EXECUTION_MODES:
        raise ValueError(
            f"{receipt_path}: execution_mode must be one of {sorted(ALLOWED_REVIEWER_EXECUTION_MODES)!r}"
        )
    if data["reviewer_invocation_kind"] not in ALLOWED_REVIEWER_INVOCATION_KINDS:
        raise ValueError(
            f"{receipt_path}: reviewer_invocation_kind must be one of {sorted(ALLOWED_REVIEWER_INVOCATION_KINDS)!r}"
        )
    if data["context_isolation_policy"] not in ALLOWED_CONTEXT_ISOLATION_POLICIES:
        raise ValueError(
            f"{receipt_path}: context_isolation_policy must be one of {sorted(ALLOWED_CONTEXT_ISOLATION_POLICIES)!r}"
        )
    if data["handoff_delivery_method"] not in ALLOWED_HANDOFF_DELIVERY_METHODS:
        raise ValueError(
            f"{receipt_path}: handoff_delivery_method must be one of {sorted(ALLOWED_HANDOFF_DELIVERY_METHODS)!r}"
        )
    if data["reviewer_context_source"] != REQUIRED_REVIEWER_CONTEXT_SOURCE:
        raise ValueError(
            f"{receipt_path}: reviewer_context_source must be {REQUIRED_REVIEWER_CONTEXT_SOURCE!r}"
        )
    if data["reviewer_history_inheritance"] != REQUIRED_REVIEWER_HISTORY_INHERITANCE:
        raise ValueError(
            f"{receipt_path}: reviewer_history_inheritance must be {REQUIRED_REVIEWER_HISTORY_INHERITANCE!r}"
        )
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
        "reviewer_agent_id": _require_string(payload, "reviewer_agent_id", path=result_path),
        "reviewer_execution_mode": _require_string(payload, "reviewer_execution_mode", path=result_path),
        "reviewer_context_source": _require_string(payload, "reviewer_context_source", path=result_path),
        "reviewer_history_inheritance": _require_string(payload, "reviewer_history_inheritance", path=result_path),
        "handoff_manifest_digest": _require_string(payload, "handoff_manifest_digest", path=result_path),
        "review_loop_outcome": outcome,
        "reviewed_program_dir": _require_string(payload, "reviewed_program_dir", path=result_path),
        "reviewed_program_entrypoint": _require_string(payload, "reviewed_program_entrypoint", path=result_path),
        "reviewed_artifact_paths": _require_string_list(payload, "reviewed_artifact_paths", path=result_path),
        "reviewed_provenance_paths": _require_string_list(payload, "reviewed_provenance_paths", path=result_path),
        "reviewed_project_root": _require_string(payload, "reviewed_project_root", path=result_path),
        "reviewed_lineage_root": _require_string(payload, "reviewed_lineage_root", path=result_path),
        "reviewed_stage_dir": _require_string(payload, "reviewed_stage_dir", path=result_path),
        "hard_gate_findings_acknowledged": _require_bool(
            payload,
            "hard_gate_findings_acknowledged",
            path=result_path,
        ),
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
    final_verdict = payload.get("final_verdict")
    if isinstance(final_verdict, str) and final_verdict.strip():
        data["final_verdict"] = final_verdict.strip()
    hard_gate_downgrade_detected = payload.get("hard_gate_downgrade_detected")
    if isinstance(hard_gate_downgrade_detected, bool):
        data["hard_gate_downgrade_detected"] = hard_gate_downgrade_detected
    hard_gate_downgrade_code = payload.get("hard_gate_downgrade_code")
    if isinstance(hard_gate_downgrade_code, str) and hard_gate_downgrade_code.strip():
        data["hard_gate_downgrade_code"] = hard_gate_downgrade_code.strip()
    for timestamp_key in ("review_started_at", "review_completed_at"):
        value = payload.get(timestamp_key)
        if isinstance(value, str) and value.strip():
            data[timestamp_key] = value.strip()
    return data


def load_final_review(path: str | Path) -> dict[str, Any]:
    final_review_path = Path(path)
    payload = _require_mapping(final_review_path)
    verdict = _require_string(payload, "verdict", path=final_review_path)
    if verdict not in ALLOWED_FINAL_REVIEW_VERDICTS:
        raise ValueError(f"{final_review_path}: unsupported verdict {verdict!r}")

    data = {
        "lineage_id": _require_string(payload, "lineage_id", path=final_review_path),
        "stage_id": _require_string(payload, "stage_id", path=final_review_path),
        "reviewer_identity": _require_string(payload, "reviewer_identity", path=final_review_path),
        "reviewer_agent_id": _require_string(payload, "reviewer_agent_id", path=final_review_path),
        "reviewed_artifact_paths": _require_non_empty_string_list(
            payload,
            "reviewed_artifact_paths",
            path=final_review_path,
        ),
        "reviewed_program_path": _require_string(payload, "reviewed_program_path", path=final_review_path),
        "reviewed_artifact_digest": _require_string(payload, "reviewed_artifact_digest", path=final_review_path),
        "reviewed_program_digest": _require_string(payload, "reviewed_program_digest", path=final_review_path),
        "verdict": verdict,
        "review_summary": _require_string(payload, "review_summary", path=final_review_path),
        "blocking_findings": _require_string_list(payload, "blocking_findings", path=final_review_path),
        "reservation_findings": _require_string_list(payload, "reservation_findings", path=final_review_path),
        "info_findings": _require_string_list(payload, "info_findings", path=final_review_path),
        "residual_risks": _require_string_list(payload, "residual_risks", path=final_review_path),
        "allowed_modifications": _require_string_list(payload, "allowed_modifications", path=final_review_path),
        "downstream_permissions": _require_string_list(payload, "downstream_permissions", path=final_review_path),
        "recommended_next_action": _require_string(payload, "recommended_next_action", path=final_review_path),
    }
    rollback_stage = _require_nullable_string(payload, "rollback_stage", path=final_review_path)
    if rollback_stage is not None:
        data["rollback_stage"] = rollback_stage
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
        "reviewer_agent_id": result_payload["reviewer_agent_id"],
        "reviewer_execution_mode": result_payload["reviewer_execution_mode"],
        "reviewer_context_source": result_payload["reviewer_context_source"],
        "reviewer_history_inheritance": result_payload["reviewer_history_inheritance"],
        "handoff_manifest_digest": result_payload["handoff_manifest_digest"],
        "review_loop_outcome": result_payload["review_loop_outcome"],
        "reviewed_program_dir": request_payload["required_program_dir"],
        "reviewed_program_entrypoint": request_payload["required_program_entrypoint"],
        "reviewed_project_root": request_payload["project_root"],
        "reviewed_lineage_root": request_payload["lineage_root"],
        "reviewed_stage_dir": request_payload["stage_dir"],
        "hard_gate_findings_acknowledged": result_payload["hard_gate_findings_acknowledged"],
        "reviewed_artifact_paths": stage_content_artifact_paths_from_request(request_payload),
        "reviewed_provenance_paths": stage_content_provenance_paths_from_request(request_payload),
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
        raise ValueError("runtime reviewer identity does not match reviewer_receipt.yaml")
    if receipt_payload["requested_reviewer_session_id"] != runtime_identity.reviewer_session_id:
        raise ValueError("runtime reviewer session does not match reviewer_receipt.yaml")


def validate_receipt_contract(
    *,
    request_payload: dict[str, Any],
    receipt_payload: dict[str, Any],
) -> None:
    if receipt_payload["review_cycle_id"] != request_payload["review_cycle_id"]:
        raise ValueError("reviewer_receipt.yaml review_cycle_id does not match the active request")
    for key in RECEIPT_CANONICAL_CONTEXT_FIELDS:
        if receipt_payload[key] != request_payload[key]:
            raise ValueError(f"reviewer_receipt.yaml {key} does not match the active request")
    if receipt_payload["launcher_owner"] != RUNTIME_LAUNCHER_OWNER:
        raise ValueError("reviewer_receipt.yaml launcher_owner is not the fixed runtime launcher")
    if receipt_payload["host"] not in ALLOWED_HOSTS:
        raise ValueError(f"reviewer_receipt.yaml host must be one of {sorted(ALLOWED_HOSTS)!r}")
    if receipt_payload["execution_mode"] not in ALLOWED_REVIEWER_EXECUTION_MODES:
        raise ValueError(
            "reviewer_receipt.yaml execution_mode must be a supported review execution mode"
        )
    if receipt_payload["reviewer_invocation_kind"] not in ALLOWED_REVIEWER_INVOCATION_KINDS:
        raise ValueError(
            "reviewer_receipt.yaml reviewer_invocation_kind must be a supported invocation kind"
        )
    if receipt_payload["context_isolation_policy"] not in ALLOWED_CONTEXT_ISOLATION_POLICIES:
        raise ValueError(
            "reviewer_receipt.yaml context_isolation_policy must be a supported isolation policy"
        )
    if receipt_payload["handoff_delivery_method"] not in ALLOWED_HANDOFF_DELIVERY_METHODS:
        raise ValueError(
            "reviewer_receipt.yaml handoff_delivery_method must be a supported handoff delivery method"
        )
    if receipt_payload.get("reviewer_context_source") != REQUIRED_REVIEWER_CONTEXT_SOURCE:
        raise ValueError("reviewer_receipt.yaml reviewer_context_source must be explicit_handoff_only")
    if receipt_payload.get("reviewer_history_inheritance") != REQUIRED_REVIEWER_HISTORY_INHERITANCE:
        raise ValueError("reviewer_receipt.yaml reviewer_history_inheritance must be none")
    expected_invocation_kind = HOST_REVIEWER_INVOCATION_KIND.get(receipt_payload["host"])
    if receipt_payload["reviewer_invocation_kind"] != expected_invocation_kind:
        raise ValueError(
            f"reviewer_receipt.yaml reviewer_invocation_kind {receipt_payload['reviewer_invocation_kind']!r} "
            f"does not match expected {expected_invocation_kind!r} for host {receipt_payload['host']!r}"
        )
    expected_isolation = HOST_CONTEXT_ISOLATION.get(receipt_payload["host"])
    if receipt_payload["context_isolation_policy"] != expected_isolation:
        raise ValueError(
            f"reviewer_receipt.yaml context_isolation_policy {receipt_payload['context_isolation_policy']!r} "
            f"does not match expected {expected_isolation!r} for host {receipt_payload['host']!r}"
        )
    expected_handoff = HOST_HANDOFF_DELIVERY.get(receipt_payload["host"])
    if receipt_payload["handoff_delivery_method"] != expected_handoff:
        raise ValueError(
            f"reviewer_receipt.yaml handoff_delivery_method {receipt_payload['handoff_delivery_method']!r} "
            f"does not match expected {expected_handoff!r} for host {receipt_payload['host']!r}"
        )
    if not receipt_payload["reviewer_agent_id"].strip():
        raise ValueError("reviewer_receipt.yaml reviewer_agent_id must be a non-empty string")
    if not receipt_payload["launcher_thread_id"].strip():
        raise ValueError("reviewer_receipt.yaml launcher_thread_id must be a non-empty string")
    if receipt_payload["write_root"] != request_payload.get("required_reviewer_write_path", REQUIRED_REVIEWER_WRITE_PATH):
        raise ValueError("reviewer_receipt.yaml write_root does not match the active request")
    if receipt_payload["handoff_manifest_path"] != request_payload["handoff_manifest_path"]:
        raise ValueError("reviewer_receipt.yaml handoff_manifest_path does not match the active request")
    if receipt_payload["handoff_manifest_digest"] != request_payload["handoff_manifest_digest"]:
        raise ValueError("reviewer_receipt.yaml handoff_manifest_digest does not match the active request")


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
    for result_key, request_key in (
        ("reviewed_project_root", "project_root"),
        ("reviewed_lineage_root", "lineage_root"),
        ("reviewed_stage_dir", "stage_dir"),
    ):
        if result_payload[result_key] != request_payload[request_key]:
            raise ValueError(
                f"{REVIEW_CONTEXT_ROOT_MISMATCH}: adversarial_review_result.yaml {result_key} "
                f"does not match adversarial_review_request.yaml"
            )
    if result_payload["hard_gate_findings_acknowledged"] is not True:
        raise ValueError("adversarial_review_result.yaml hard_gate_findings_acknowledged must be true")
    if sorted(result_payload["reviewed_artifact_paths"]) != stage_content_artifact_paths_from_request(request_payload):
        raise ValueError("adversarial_review_result.yaml reviewed_artifact_paths do not cover the stage content artifacts")
    if sorted(result_payload["reviewed_provenance_paths"]) != stage_content_provenance_paths_from_request(request_payload):
        raise ValueError(
            "adversarial_review_result.yaml reviewed_provenance_paths do not cover the stage content provenance files"
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
        raise ValueError("adversarial_review_result.yaml reviewer_identity does not match reviewer_receipt.yaml")
    if receipt_payload["requested_reviewer_session_id"] != result_payload["reviewer_session_id"]:
        raise ValueError("adversarial_review_result.yaml reviewer_session_id does not match reviewer_receipt.yaml")
    if receipt_payload["reviewer_agent_id"] != result_payload["reviewer_agent_id"]:
        raise ValueError("adversarial_review_result.yaml reviewer_agent_id does not match reviewer_receipt.yaml")
    if result_payload["reviewer_execution_mode"] not in ALLOWED_REVIEWER_EXECUTION_MODES:
        raise ValueError(
            "adversarial_review_result.yaml reviewer_execution_mode must be a supported review execution mode"
        )
    if result_payload["reviewer_execution_mode"] != receipt_payload["execution_mode"]:
        raise ValueError(
            "adversarial_review_result.yaml reviewer_execution_mode does not match reviewer_receipt.yaml"
        )
    if result_payload["reviewer_context_source"] != receipt_payload["reviewer_context_source"]:
        raise ValueError("adversarial_review_result.yaml reviewer_context_source does not match reviewer_receipt.yaml")
    if result_payload["reviewer_history_inheritance"] != receipt_payload["reviewer_history_inheritance"]:
        raise ValueError(
            "adversarial_review_result.yaml reviewer_history_inheritance does not match reviewer_receipt.yaml"
        )
    if result_payload["handoff_manifest_digest"] != request_payload["handoff_manifest_digest"]:
        raise ValueError("adversarial_review_result.yaml handoff_manifest_digest does not match the active request")
    if result_payload["handoff_manifest_digest"] != receipt_payload["handoff_manifest_digest"]:
        raise ValueError("adversarial_review_result.yaml handoff_manifest_digest does not match reviewer_receipt.yaml")
