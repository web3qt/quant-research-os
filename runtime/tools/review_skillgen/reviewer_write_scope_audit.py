from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    SPAWNED_REVIEWER_RECEIPT_FILENAME,
    load_adversarial_review_result,
    load_spawned_reviewer_receipt,
)
from runtime.tools.review_skillgen.review_cycle_trace import (
    REVIEW_CYCLE_TRACE_FILENAME,
    append_review_cycle_event,
)


REVIEWER_WRITE_SCOPE_BASELINE_FILENAME = "reviewer_write_scope_baseline.yaml"
REVIEWER_WRITE_SCOPE_AUDIT_FILENAME = "reviewer_write_scope_audit.yaml"
REVIEW_RESULT_ROOT = Path("review/result")
ALLOWED_RESULT_FILENAMES = {
    ADVERSARIAL_REVIEW_RESULT_FILENAME,
    "review_findings.yaml",
    REVIEWER_WRITE_SCOPE_AUDIT_FILENAME,
}


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _baseline_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "request" / REVIEWER_WRITE_SCOPE_BASELINE_FILENAME


def _audit_path(stage_dir: Path) -> Path:
    return stage_dir / "review" / "result" / REVIEWER_WRITE_SCOPE_AUDIT_FILENAME


def _iter_protected_files(stage_dir: Path) -> dict[str, str]:
    baseline_rel = Path("review/request") / REVIEWER_WRITE_SCOPE_BASELINE_FILENAME
    trace_rel = Path("review") / REVIEW_CYCLE_TRACE_FILENAME
    snapshot: dict[str, str] = {}
    for path in sorted(stage_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(stage_dir)
        if rel == baseline_rel:
            continue
        if rel == trace_rel:
            continue
        if rel.parts[:2] == REVIEW_RESULT_ROOT.parts:
            continue
        snapshot[rel.as_posix()] = _hash_file(path)
    return snapshot


def write_reviewer_write_scope_baseline(
    stage_dir: Path,
    *,
    review_cycle_id: str,
    launcher_thread_id: str,
    spawned_agent_id: str,
) -> dict[str, Any]:
    path = _baseline_path(stage_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "review_cycle_id": review_cycle_id,
        "launcher_thread_id": launcher_thread_id,
        "spawned_agent_id": spawned_agent_id,
        "excluded_roots": [REVIEW_RESULT_ROOT.as_posix()],
        "protected_snapshot": _iter_protected_files(stage_dir),
        "baseline_written_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return payload


def load_reviewer_write_scope_baseline(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must load to a mapping")
    for key in ("review_cycle_id", "launcher_thread_id", "spawned_agent_id", "baseline_written_at"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{path}: {key} must be a non-empty string")
    snapshot = payload.get("protected_snapshot")
    if not isinstance(snapshot, dict) or not all(
        isinstance(k, str) and isinstance(v, str) and k and v for k, v in snapshot.items()
    ):
        raise ValueError(f"{path}: protected_snapshot must be a string-to-string mapping")
    return payload


def load_reviewer_write_scope_audit(path: str | Path) -> dict[str, Any]:
    audit_path = Path(path)
    if not audit_path.exists():
        raise ValueError(f"{audit_path}: {REVIEWER_WRITE_SCOPE_AUDIT_FILENAME} is missing")
    payload = yaml.safe_load(audit_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must load to a mapping")
    for key in ("review_cycle_id", "launcher_thread_id", "spawned_agent_id", "audit_status", "audited_at"):
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{path}: {key} must be a non-empty string")
    for key in ("protected_files_added", "protected_files_removed", "protected_files_changed", "unexpected_result_files"):
        value = payload.get(key)
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            raise ValueError(f"{path}: {key} must be a list of non-empty strings")
    return payload


def run_reviewer_write_scope_audit(stage_dir: Path) -> dict[str, Any]:
    stage_dir = stage_dir.resolve()
    receipt = load_spawned_reviewer_receipt(stage_dir / "review" / "request" / SPAWNED_REVIEWER_RECEIPT_FILENAME)
    baseline = load_reviewer_write_scope_baseline(_baseline_path(stage_dir))
    result = load_adversarial_review_result(stage_dir / "review" / "result" / ADVERSARIAL_REVIEW_RESULT_FILENAME)

    before = dict(baseline["protected_snapshot"])
    after = _iter_protected_files(stage_dir)
    removed = sorted(path for path in before if path not in after)
    added = sorted(path for path in after if path not in before)
    changed = sorted(path for path in before if path in after and before[path] != after[path])

    result_dir = stage_dir / REVIEW_RESULT_ROOT
    unexpected_result_files = sorted(
        rel.name for rel in result_dir.glob("*") if rel.is_file() and rel.name not in ALLOWED_RESULT_FILENAMES
    )

    audit_status = "PASS" if not removed and not added and not changed and not unexpected_result_files else "FAIL"
    payload = {
        "review_cycle_id": receipt["review_cycle_id"],
        "launcher_thread_id": receipt["launcher_thread_id"],
        "spawned_agent_id": receipt["spawned_agent_id"],
        "reviewer_agent_id": result["reviewer_agent_id"],
        "audit_status": audit_status,
        "protected_files_added": added,
        "protected_files_removed": removed,
        "protected_files_changed": changed,
        "unexpected_result_files": unexpected_result_files,
        "audited_at": datetime.now(timezone.utc).isoformat(),
    }
    path = _audit_path(stage_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    append_review_cycle_event(
        stage_dir,
        event_type="write_scope_audit_completed",
        review_cycle_id=payload["review_cycle_id"],
        payload={
            "launcher_thread_id": payload["launcher_thread_id"],
            "spawned_agent_id": payload["spawned_agent_id"],
            "reviewer_agent_id": payload["reviewer_agent_id"],
            "audit_status": payload["audit_status"],
            "protected_files_added": list(payload["protected_files_added"]),
            "protected_files_removed": list(payload["protected_files_removed"]),
            "protected_files_changed": list(payload["protected_files_changed"]),
            "unexpected_result_files": list(payload["unexpected_result_files"]),
        },
    )
    return payload


def validate_reviewer_write_scope_audit(
    *,
    receipt_payload: dict[str, Any],
    audit_payload: dict[str, Any],
) -> None:
    if audit_payload["review_cycle_id"] != receipt_payload["review_cycle_id"]:
        raise ValueError("reviewer_write_scope_audit.yaml review_cycle_id does not match spawned_reviewer_receipt.yaml")
    if audit_payload["launcher_thread_id"] != receipt_payload["launcher_thread_id"]:
        raise ValueError("reviewer_write_scope_audit.yaml launcher_thread_id does not match spawned_reviewer_receipt.yaml")
    if audit_payload["spawned_agent_id"] != receipt_payload["spawned_agent_id"]:
        raise ValueError("reviewer_write_scope_audit.yaml spawned_agent_id does not match spawned_reviewer_receipt.yaml")
    if audit_payload["audit_status"] != "PASS":
        raise ValueError("reviewer_write_scope_audit.yaml audit_status must be PASS before closure")
