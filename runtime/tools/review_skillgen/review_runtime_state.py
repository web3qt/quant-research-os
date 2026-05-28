from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Sequence

import yaml

from runtime.tools.artifact_digest_manifest import (
    ARTIFACT_DIGEST_MANIFEST_FILENAME,
    HOT_PATH_CONTENT_HASH_BANNED_SUFFIXES,
)
from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
)
from runtime.tools.review_skillgen.review_scope import normalize_review_paths


REVIEW_RUNTIME_STATE_FILENAME = "review_runtime_state.yaml"
MATERIALIZATION_DIGEST_LEDGER_FILENAME = "materialization_digest_ledger.yaml"
LARGE_ARTIFACT_CONTENT_DIGEST_LIMIT_BYTES = 64 * 1024 * 1024
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REVIEW_RUNTIME_STATE_ALLOWED_VALUES = {
    "review_not_started",
    "review_in_progress",
    "awaiting_author_fix",
    "review_closed_pass",
    "review_closed_nonadvancing",
}
_ACTIVE_REQUEST_FILES = (
    "adversarial_review_request.yaml",
    "reviewer_handoff_manifest.yaml",
    "reviewer_receipt.yaml",
    "reviewer_write_scope_baseline.yaml",
)
_ACTIVE_REVIEW_ROOT_FILES = (
    "final_review.yaml",
)
_ACTIVE_RESULT_FILES = (
    "review_findings.yaml",
    "reviewer_findings.raw.yaml",
    "adversarial_review_result.yaml",
    "reviewer_write_scope_audit.yaml",
)
_ACTIVE_CLOSURE_FILES = (
    "latest_review_pack.yaml",
    "stage_gate_review.yaml",
    "stage_completion_certificate.yaml",
)


def review_runtime_state_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "state" / REVIEW_RUNTIME_STATE_FILENAME


def materialization_digest_ledger_path_from_artifact_root(artifact_root: Path) -> Path:
    resolved = artifact_root.resolve()
    if resolved.name == "formal" and resolved.parent.name == "author":
        stage_dir = resolved.parents[1]
    else:
        stage_dir = resolved
    return stage_dir / "review" / "state" / MATERIALIZATION_DIGEST_LEDGER_FILENAME


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


def _content_hash_requires_manifest(path: Path) -> bool:
    if path.suffix.lower() in HOT_PATH_CONTENT_HASH_BANNED_SUFFIXES:
        return True
    return path.stat().st_size > LARGE_ARTIFACT_CONTENT_DIGEST_LIMIT_BYTES


def _archive_file_tree(
    stage_dir: Path,
    src_root: Path,
    dst_root: Path,
    *,
    review_cycle_id: str,
    reason: str,
    timestamp: str,
) -> list[str]:
    written: list[str] = []
    if not src_root.exists():
        return written

    for src in sorted(path for path in src_root.rglob("*") if path.is_file()):
        rel = src.relative_to(src_root)
        stem = src.stem
        suffix = "".join(src.suffixes)
        dst = dst_root / rel.parent / f"{stem}.{review_cycle_id}.{reason}.{timestamp}{suffix}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        written.append(str(dst.relative_to(stage_dir)))

    for directory in sorted((path for path in src_root.rglob("*") if path.is_dir()), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass

    return written


def _archive_named_files(
    stage_dir: Path,
    src_root: Path,
    dst_root: Path,
    *,
    filenames: Sequence[str],
    review_cycle_id: str,
    reason: str,
    timestamp: str,
) -> list[str]:
    written: list[str] = []
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
    return written


def _load_materialization_digest_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"files": {}}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {"files": {}}
    files = payload.get("files")
    if not isinstance(files, dict):
        payload["files"] = {}
    return payload


def _write_materialization_digest_ledger(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _file_cache_metadata(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "kind": "file",
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _cached_file_digest(path: Path, *, root: Path, ledger: dict[str, Any]) -> str:
    rel = path.relative_to(root).as_posix()
    files = ledger.setdefault("files", {})
    metadata = _file_cache_metadata(path)
    cached = files.get(rel)
    if isinstance(cached, dict) and cached.get("metadata") == metadata:
        digest = cached.get("digest")
        if isinstance(digest, str) and digest:
            return digest

    digest = _file_digest(path)
    files[rel] = {
        "metadata": metadata,
        "digest": digest,
    }
    return digest


def _load_artifact_digest_manifest(root: Path) -> dict[str, Any]:
    path = root / ARTIFACT_DIGEST_MANIFEST_FILENAME
    if not path.exists():
        raise ValueError(f"ARTIFACT_DIGEST_MANIFEST_MISSING: {path} is required for data or large artifacts")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: artifact digest manifest must load to a mapping")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError(f"{path}: artifacts must be a list")

    program_hash = payload.get("program_hash")
    provenance_path = root / "program_execution_manifest.json"
    if isinstance(program_hash, str) and program_hash.strip() and provenance_path.exists():
        provenance = yaml.safe_load(provenance_path.read_text(encoding="utf-8")) or {}
        if isinstance(provenance, dict):
            provenance_program_hash = provenance.get("program_hash")
            if (
                isinstance(provenance_program_hash, str)
                and provenance_program_hash.strip()
                and provenance_program_hash != program_hash
            ):
                raise ValueError(
                    "ARTIFACT_DIGEST_MANIFEST_STALE: manifest program_hash does not match "
                    "program_execution_manifest.json"
                )
    return payload


def _manifest_artifact_digest(path: Path, *, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    manifest = _load_artifact_digest_manifest(root)
    matching_entry = None
    for item in manifest["artifacts"]:
        if isinstance(item, dict) and item.get("path") == rel:
            matching_entry = item
            break
    if matching_entry is None:
        raise ValueError(f"ARTIFACT_DIGEST_MANIFEST_INCOMPLETE: missing digest entry for {rel}")

    algorithm = matching_entry.get("digest_algorithm")
    digest = matching_entry.get("sha256")
    size_bytes = matching_entry.get("size_bytes")
    if algorithm != "sha256" or not isinstance(digest, str) or _SHA256_RE.match(digest) is None:
        raise ValueError(f"ARTIFACT_DIGEST_MANIFEST_INVALID: invalid sha256 digest entry for {rel}")
    if not isinstance(size_bytes, int) or size_bytes < 0:
        raise ValueError(f"ARTIFACT_DIGEST_MANIFEST_INVALID: invalid size_bytes for {rel}")
    if path.exists() and path.stat().st_size != size_bytes:
        raise ValueError(f"ARTIFACT_DIGEST_MANIFEST_STALE: size_bytes mismatch for {rel}")

    return _digest_bytes(
        [
            b"MANIFEST_ARTIFACT:",
            rel.encode("utf-8"),
            b"\0",
            digest.encode("utf-8"),
            b"\0",
            str(size_bytes).encode("utf-8"),
        ]
    )


def _path_digest(path: Path, *, root: Path, ledger: dict[str, Any] | None = None) -> str:
    if path.is_file():
        rel = path.relative_to(root).as_posix().encode("utf-8")
        if _content_hash_requires_manifest(path):
            file_digest = _manifest_artifact_digest(path, root=root)
        else:
            file_digest = (
                _cached_file_digest(path, root=root, ledger=ledger)
                if ledger is not None
                else _file_digest(path)
            )
        return _digest_bytes([b"FILE:", rel, b"\0", file_digest.encode("utf-8")])

    if path.is_dir():
        parts: list[bytes] = [b"DIR:", path.relative_to(root).as_posix().encode("utf-8"), b"\0"]
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            rel = child.relative_to(root).as_posix().encode("utf-8")
            if _content_hash_requires_manifest(child):
                file_digest = _manifest_artifact_digest(child, root=root)
            else:
                file_digest = (
                    _cached_file_digest(child, root=root, ledger=ledger)
                    if ledger is not None
                    else _file_digest(child)
                )
            parts.extend([rel, b"\0", file_digest.encode("utf-8"), b"\0"])
        return _digest_bytes(parts)

    return _digest_bytes([b"MISSING:", path.relative_to(root).as_posix().encode("utf-8")])


def compute_author_materialization_digest(
    *,
    artifact_root: Path,
    required_outputs: Sequence[str],
    required_provenance_paths: Sequence[str] = ("program_execution_manifest.json",),
) -> str:
    artifact_root = artifact_root.resolve()
    ledger_path = materialization_digest_ledger_path_from_artifact_root(artifact_root)
    ledger = _load_materialization_digest_ledger(ledger_path)
    parts: list[bytes] = []
    for name in normalize_review_paths(required_outputs) + normalize_review_paths(required_provenance_paths):
        target = artifact_root / name
        parts.extend(
            [
                name.encode("utf-8"),
                b"\0",
                _path_digest(target, root=artifact_root, ledger=ledger).encode("utf-8"),
                b"\0",
            ]
        )
    materialization_digest = _digest_bytes(parts)
    ledger["materialization_digest"] = materialization_digest
    ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_materialization_digest_ledger(ledger_path, ledger)
    return materialization_digest


def compute_author_materialization_digest_fresh(
    *,
    artifact_root: Path,
    required_outputs: Sequence[str],
    required_provenance_paths: Sequence[str] = ("program_execution_manifest.json",),
) -> str:
    artifact_root = artifact_root.resolve()
    parts: list[bytes] = []
    for name in normalize_review_paths(required_outputs) + normalize_review_paths(required_provenance_paths):
        target = artifact_root / name
        parts.extend(
            [
                name.encode("utf-8"),
                b"\0",
                _path_digest(target, root=artifact_root, ledger=None).encode("utf-8"),
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
        ("closure", _ACTIVE_CLOSURE_FILES),
    ):
        src_root = stage_dir / "review" / subdir_name
        dst_root = archive_root / subdir_name
        written.extend(
            _archive_named_files(
                stage_dir,
                src_root,
                dst_root,
                filenames=filenames,
                review_cycle_id=review_cycle_id,
                reason=reason,
                timestamp=timestamp,
            )
        )

    review_root = stage_dir / "review"
    review_archive_root = archive_root / "review"
    written.extend(
        _archive_named_files(
            stage_dir,
            review_root,
            review_archive_root,
            filenames=_ACTIVE_REVIEW_ROOT_FILES,
            review_cycle_id=review_cycle_id,
            reason=reason,
            timestamp=timestamp,
        )
    )

    result_src_root = stage_dir / "review" / "result"
    result_dst_root = archive_root / "result"
    written.extend(
        _archive_named_files(
            stage_dir,
            result_src_root,
            result_dst_root,
            filenames=_ACTIVE_RESULT_FILES,
            review_cycle_id=review_cycle_id,
            reason=reason,
            timestamp=timestamp,
        )
    )
    written.extend(
        _archive_file_tree(
            stage_dir,
            result_src_root,
            result_dst_root,
            review_cycle_id=review_cycle_id,
            reason=reason,
            timestamp=timestamp,
        )
    )

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
