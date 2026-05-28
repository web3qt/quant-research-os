from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


ARTIFACT_DIGEST_MANIFEST_FILENAME = "artifact_digest_manifest.json"
HOT_PATH_CONTENT_HASH_BANNED_SUFFIXES = {
    ".arrow",
    ".avro",
    ".feather",
    ".h5",
    ".hdf5",
    ".ipc",
    ".npy",
    ".npz",
    ".orc",
    ".parquet",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_artifact_digest_manifest(
    *,
    artifact_root: Path,
    lineage_id: str,
    stage_id: str,
    program_hash: str,
    artifact_paths: Sequence[str],
    program_execution_manifest_path: str = "program_execution_manifest.json",
) -> Path:
    artifact_root = artifact_root.resolve()
    generated_at = datetime.now(timezone.utc).isoformat()
    artifacts: list[dict[str, object]] = []
    for artifact_path in artifact_paths:
        relpath = artifact_path.strip()
        if not relpath:
            continue
        path = artifact_root / relpath
        if not path.exists() or not path.is_file():
            raise ValueError(f"{relpath}: artifact digest manifest can only include existing files")
        artifacts.append(
            {
                "path": relpath,
                "size_bytes": path.stat().st_size,
                "digest_algorithm": "sha256",
                "sha256": file_sha256(path),
                "artifact_kind": "machine",
                "generated_at": generated_at,
            }
        )

    payload = {
        "schema_version": 1,
        "lineage_id": lineage_id,
        "stage_id": stage_id,
        "program_hash": program_hash,
        "program_execution_manifest_path": program_execution_manifest_path,
        "artifacts": artifacts,
    }
    manifest_path = artifact_root / ARTIFACT_DIGEST_MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path
