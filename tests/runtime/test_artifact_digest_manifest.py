from __future__ import annotations

import json
from pathlib import Path

from runtime.tools.artifact_digest_manifest import write_artifact_digest_manifest
from runtime.tools.review_skillgen import review_runtime_state


def test_write_artifact_digest_manifest_supports_data_artifact_materialization(tmp_path: Path, monkeypatch) -> None:
    formal_dir = tmp_path / "02_tss_data_ready" / "author" / "formal"
    formal_dir.mkdir(parents=True)
    parquet_path = formal_dir / "asset_time_index.parquet"
    parquet_path.write_bytes(b"parquet-bytes")
    (formal_dir / "program_execution_manifest.json").write_text(
        json.dumps({"program_hash": "program-hash"}, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest_path = write_artifact_digest_manifest(
        artifact_root=formal_dir,
        lineage_id="digest-case",
        stage_id="tss_data_ready",
        program_hash="program-hash",
        artifact_paths=["asset_time_index.parquet"],
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["program_hash"] == "program-hash"
    assert payload["artifacts"][0]["path"] == "asset_time_index.parquet"
    assert payload["artifacts"][0]["size_bytes"] == len(b"parquet-bytes")
    assert len(payload["artifacts"][0]["sha256"]) == 64

    def reject_parquet_digest(path: Path) -> str:
        if path.name == "asset_time_index.parquet":
            raise AssertionError("runtime materialization must use the manifest, not read parquet")
        return "small-file-digest"

    monkeypatch.setattr(review_runtime_state, "_file_digest", reject_parquet_digest)

    digest = review_runtime_state.compute_author_materialization_digest_fresh(
        artifact_root=formal_dir,
        required_outputs=["asset_time_index.parquet"],
        required_provenance_paths=["program_execution_manifest.json"],
    )

    assert len(digest) == 64
