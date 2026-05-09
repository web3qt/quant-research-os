from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import yaml


LINEAGE_LOCK_LEDGER_FILENAME = "lineage_lock_ledger.yaml"
FROZEN_ARTIFACT_MUTATED = "FROZEN_ARTIFACT_MUTATED"
PASS_LIKE_FINAL_VERDICTS = {"PASS", "CONDITIONAL PASS", "GO", "PASS FOR RETRY", "RETRY"}
CLOSURE_FILENAMES = (
    "latest_review_pack.yaml",
    "stage_completion_certificate.yaml",
    "stage_gate_review.yaml",
)


@dataclass(frozen=True)
class FrozenArtifactMutationError(RuntimeError):
    lineage_id: str
    locked_stage: str
    path: str
    expected_sha256: str | None
    observed_sha256: str | None
    lock_reason: str

    @property
    def reason_code(self) -> str:
        return FROZEN_ARTIFACT_MUTATED

    @property
    def next_action(self) -> str:
        return (
            f"Frozen upstream artifact changed. Restore {self.path} to the locked version, "
            "or open a child lineage if this frozen fact change is intentional."
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "reason_code": self.reason_code,
            "lineage_id": self.lineage_id,
            "locked_stage": self.locked_stage,
            "path": self.path,
            "expected_sha256": self.expected_sha256,
            "observed_sha256": self.observed_sha256,
            "lock_reason": self.lock_reason,
            "next_action": self.next_action,
        }

    def __str__(self) -> str:
        return (
            f"{self.reason_code}: {self.path} changed for locked stage {self.locked_stage}; "
            f"expected={self.expected_sha256} observed={self.observed_sha256}. {self.next_action}"
        )


def ledger_path(lineage_root: Path) -> Path:
    return lineage_root / LINEAGE_LOCK_LEDGER_FILENAME


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _empty_ledger(lineage_root: Path) -> dict[str, Any]:
    return {
        "ledger_version": 1,
        "lineage_id": lineage_root.name,
        "locked_stages": {},
    }


def load_lineage_lock_ledger(lineage_root: Path) -> dict[str, Any]:
    path = ledger_path(lineage_root)
    if not path.exists():
        return _empty_ledger(lineage_root)
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return _empty_ledger(lineage_root)
    if payload.get("ledger_version") != 1:
        payload["ledger_version"] = 1
    if not isinstance(payload.get("lineage_id"), str) or not payload.get("lineage_id"):
        payload["lineage_id"] = lineage_root.name
    if not isinstance(payload.get("locked_stages"), dict):
        payload["locked_stages"] = {}
    return payload


def _write_lineage_lock_ledger(lineage_root: Path, payload: dict[str, Any]) -> None:
    path = ledger_path(lineage_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _relative_to_lineage(lineage_root: Path, path: Path) -> str:
    return path.resolve().relative_to(lineage_root.resolve()).as_posix()


def _observed_digest(lineage_root: Path, rel_path: str) -> str | None:
    path = lineage_root / rel_path
    if not path.exists() or not path.is_file():
        return None
    return _sha256_file(path)


def _locked_file_records(
    *,
    lineage_root: Path,
    stage_dir: Path,
    required_artifact_paths: Sequence[str],
    required_provenance_paths: Sequence[str],
) -> list[dict[str, str]]:
    author_formal_dir = stage_dir / "author" / "formal"
    review_closure_dir = stage_dir / "review" / "closure"
    records: list[dict[str, str]] = []

    for name in sorted(set(required_artifact_paths) | set(required_provenance_paths)):
        path = author_formal_dir / name
        if not path.exists() or not path.is_file():
            continue
        records.append(
            {
                "path": _relative_to_lineage(lineage_root, path),
                "sha256": _sha256_file(path),
                "artifact_role": "author_formal",
            }
        )

    for filename in CLOSURE_FILENAMES:
        path = review_closure_dir / filename
        if not path.exists() or not path.is_file():
            continue
        records.append(
            {
                "path": _relative_to_lineage(lineage_root, path),
                "sha256": _sha256_file(path),
                "artifact_role": "review_closure",
            }
        )

    return sorted(records, key=lambda item: item["path"])


def _raise_mutation(
    *,
    lineage_root: Path,
    locked_stage: str,
    path: str,
    expected_sha256: str | None,
    observed_sha256: str | None,
    lock_reason: str,
) -> None:
    raise FrozenArtifactMutationError(
        lineage_id=lineage_root.name,
        locked_stage=locked_stage,
        path=path,
        expected_sha256=expected_sha256,
        observed_sha256=observed_sha256,
        lock_reason=lock_reason,
    )


def assert_lineage_locks_intact(lineage_root: Path) -> None:
    ledger = load_lineage_lock_ledger(lineage_root)
    locked_stages = ledger.get("locked_stages", {})
    if not isinstance(locked_stages, dict):
        return
    for stage, stage_payload in sorted(locked_stages.items()):
        if not isinstance(stage_payload, dict):
            continue
        lock_reason = str(stage_payload.get("lock_reason", "stage_review_closure"))
        files = stage_payload.get("files", [])
        if not isinstance(files, list):
            continue
        for record in files:
            if not isinstance(record, dict):
                continue
            rel_path = str(record.get("path", "")).strip()
            expected = str(record.get("sha256", "")).strip()
            if not rel_path or not expected:
                continue
            observed = _observed_digest(lineage_root, rel_path)
            if observed != expected:
                _raise_mutation(
                    lineage_root=lineage_root,
                    locked_stage=str(stage),
                    path=rel_path,
                    expected_sha256=expected,
                    observed_sha256=observed,
                    lock_reason=lock_reason,
                )


def _merge_locked_records(
    *,
    lineage_root: Path,
    stage: str,
    lock_reason: str,
    existing_records: list[dict[str, Any]],
    new_records: list[dict[str, str]],
) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for record in existing_records:
        if not isinstance(record, dict):
            continue
        rel_path = str(record.get("path", "")).strip()
        expected = str(record.get("sha256", "")).strip()
        role = str(record.get("artifact_role", "")).strip() or "unknown"
        if not rel_path or not expected:
            continue
        observed = _observed_digest(lineage_root, rel_path)
        if observed != expected:
            _raise_mutation(
                lineage_root=lineage_root,
                locked_stage=stage,
                path=rel_path,
                expected_sha256=expected,
                observed_sha256=observed,
                lock_reason=lock_reason,
            )
        merged[rel_path] = {
            "path": rel_path,
            "sha256": expected,
            "artifact_role": role,
        }

    for record in new_records:
        existing = merged.get(record["path"])
        if existing is not None and existing["sha256"] != record["sha256"]:
            _raise_mutation(
                lineage_root=lineage_root,
                locked_stage=stage,
                path=record["path"],
                expected_sha256=existing["sha256"],
                observed_sha256=record["sha256"],
                lock_reason=lock_reason,
            )
        merged[record["path"]] = record

    return [merged[path] for path in sorted(merged)]


def lock_reviewed_stage(
    *,
    lineage_root: Path,
    stage_dir: Path,
    stage: str,
    review_cycle_id: str,
    final_verdict: str,
    required_artifact_paths: Sequence[str],
    required_provenance_paths: Sequence[str],
    locked_at: str | None = None,
) -> dict[str, Any]:
    lineage_root = lineage_root.resolve()
    stage_dir = stage_dir.resolve()
    ledger = load_lineage_lock_ledger(lineage_root)
    if final_verdict not in PASS_LIKE_FINAL_VERDICTS:
        return ledger

    lock_reason = "stage_review_closure"
    locked_stages = ledger.setdefault("locked_stages", {})
    if not isinstance(locked_stages, dict):
        locked_stages = {}
        ledger["locked_stages"] = locked_stages

    records = _locked_file_records(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        required_artifact_paths=required_artifact_paths,
        required_provenance_paths=required_provenance_paths,
    )
    existing_stage = locked_stages.get(stage)
    if isinstance(existing_stage, dict):
        files = existing_stage.get("files", [])
        if not isinstance(files, list):
            files = []
        existing_stage["files"] = _merge_locked_records(
            lineage_root=lineage_root,
            stage=stage,
            lock_reason=str(existing_stage.get("lock_reason", lock_reason)),
            existing_records=files,
            new_records=records,
        )
    else:
        locked_stages[stage] = {
            "locked_at": locked_at or datetime.now(timezone.utc).isoformat(),
            "locked_at_review_cycle_id": review_cycle_id,
            "lock_reason": lock_reason,
            "files": records,
        }

    _write_lineage_lock_ledger(lineage_root, ledger)
    return ledger
