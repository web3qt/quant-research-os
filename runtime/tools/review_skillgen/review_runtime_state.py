from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
)


REVIEW_RUNTIME_STATE_FILENAME = "review_runtime_state.yaml"
REVIEW_RUNTIME_STATE_ALLOWED_VALUES = {
    "review_not_started",
    "review_in_progress",
    "awaiting_author_fix",
    "review_closed_pass",
    "review_closed_nonadvancing",
}
_ACTIVE_REQUEST_FILES = (
    "adversarial_review_request.yaml",
    "spawned_reviewer_handoff_manifest.yaml",
    "spawned_reviewer_receipt.yaml",
    "reviewer_write_scope_baseline.yaml",
)
_ACTIVE_RESULT_FILES = (
    "reviewer_findings.raw.yaml",
    "adversarial_review_result.yaml",
    "review_findings.yaml",
    "reviewer_write_scope_audit.yaml",
)
_ACTIVE_CLOSURE_FILES = (
    "latest_review_pack.yaml",
    "stage_gate_review.yaml",
    "stage_completion_certificate.yaml",
)


def review_runtime_state_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "state" / REVIEW_RUNTIME_STATE_FILENAME


def load_review_runtime_state(path: str | Path) -> dict[str, Any]:
    state_path = Path(path)
    if not state_path.exists():
        raise ValueError(f"{state_path}: {REVIEW_RUNTIME_STATE_FILENAME} is missing")
    payload = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{state_path}: review runtime state must load to a mapping")
    state = payload.get("review_state")
    if not isinstance(state, str) or state not in REVIEW_RUNTIME_STATE_ALLOWED_VALUES:
        raise ValueError(f"{state_path}: review_state is invalid")
    data = {
        "review_state": state,
        "active_review_cycle_id": payload.get("active_review_cycle_id"),
        "review_requested_at": payload.get("review_requested_at"),
        "review_bound_author_digest": payload.get("review_bound_author_digest"),
        "reviewer_identity": payload.get("reviewer_identity"),
        "reviewer_session_id": payload.get("reviewer_session_id"),
        "last_review_verdict": payload.get("last_review_verdict"),
        "closure_written_at": payload.get("closure_written_at"),
        "updated_at": payload.get("updated_at"),
    }
    for key, value in data.items():
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{state_path}: {key} must be a non-empty string when present")
    return data


def write_review_runtime_state(
    stage_dir: Path,
    *,
    review_state: str,
    active_review_cycle_id: str | None = None,
    review_requested_at: str | None = None,
    review_bound_author_digest: str | None = None,
    reviewer_identity: str | None = None,
    reviewer_session_id: str | None = None,
    last_review_verdict: str | None = None,
    closure_written_at: str | None = None,
) -> dict[str, Any]:
    if review_state not in REVIEW_RUNTIME_STATE_ALLOWED_VALUES:
        raise ValueError(f"unsupported review_state: {review_state}")
    state_path = review_runtime_state_path(stage_dir)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "review_state": review_state,
        "active_review_cycle_id": active_review_cycle_id,
        "review_requested_at": review_requested_at,
        "review_bound_author_digest": review_bound_author_digest,
        "reviewer_identity": reviewer_identity,
        "reviewer_session_id": reviewer_session_id,
        "last_review_verdict": last_review_verdict,
        "closure_written_at": closure_written_at,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    state_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return payload


def _digest_bytes(parts: list[bytes]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part)
    return digest.hexdigest()


def _file_digest(path: Path) -> str:
    return _digest_bytes([path.read_bytes()])


def _path_digest(path: Path, *, root: Path) -> str:
    if path.is_file():
        rel = path.relative_to(root).as_posix().encode("utf-8")
        return _digest_bytes([b"FILE:", rel, b"\0", _file_digest(path).encode("utf-8")])

    if path.is_dir():
        parts: list[bytes] = [b"DIR:", path.relative_to(root).as_posix().encode("utf-8"), b"\0"]
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            rel = child.relative_to(root).as_posix().encode("utf-8")
            parts.extend([rel, b"\0", _file_digest(child).encode("utf-8"), b"\0"])
        return _digest_bytes(parts)

    return _digest_bytes([b"MISSING:", path.relative_to(root).as_posix().encode("utf-8")])


def compute_author_materialization_digest(
    *,
    artifact_root: Path,
    required_outputs: Sequence[str],
    required_provenance_paths: Sequence[str] = ("program_execution_manifest.json",),
) -> str:
    artifact_root = artifact_root.resolve()
    parts: list[bytes] = []
    for name in list(required_outputs) + list(required_provenance_paths):
        target = artifact_root / name
        parts.extend(
            [
                name.encode("utf-8"),
                b"\0",
                _path_digest(target, root=artifact_root).encode("utf-8"),
                b"\0",
            ]
        )
    return _digest_bytes(parts)


def archive_active_review_cycle(
    stage_dir: Path,
    *,
    review_cycle_id: str,
    reason: str,
) -> list[str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_root = stage_dir / "review" / "archive"
    written: list[str] = []

    for subdir_name, filenames in (
        ("request", _ACTIVE_REQUEST_FILES),
        ("result", _ACTIVE_RESULT_FILES),
        ("closure", _ACTIVE_CLOSURE_FILES),
    ):
        src_root = stage_dir / "review" / subdir_name
        dst_root = archive_root / subdir_name
        dst_root.mkdir(parents=True, exist_ok=True)
        for filename in filenames:
            src = src_root / filename
            if not src.exists():
                continue
            stem = src.stem
            suffix = "".join(src.suffixes)
            dst = dst_root / f"{stem}.{review_cycle_id}.{reason}.{timestamp}{suffix}"
            src.rename(dst)
            written.append(str(dst.relative_to(stage_dir)))

    state_path = review_runtime_state_path(stage_dir)
    if state_path.exists():
        dst_root = archive_root / "state"
        dst_root.mkdir(parents=True, exist_ok=True)
        dst = dst_root / f"review_runtime_state.{review_cycle_id}.{reason}.{timestamp}.yaml"
        state_path.rename(dst)
        written.append(str(dst.relative_to(stage_dir)))

    return written


def request_mtime_or_none(stage_dir: Path) -> float | None:
    request_path = stage_dir / "review" / "request" / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    if not request_path.exists():
        return None
    return request_path.stat().st_mtime
