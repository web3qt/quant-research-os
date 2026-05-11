from pathlib import Path

from runtime.tools.review_skillgen import review_runtime_state


def test_compute_author_materialization_digest_reuses_unchanged_file_digest_cache(
    tmp_path: Path,
    monkeypatch,
) -> None:
    stage_dir = tmp_path / "03_csf_signal_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "factor_panel.parquet").write_bytes(b"large-artifact-bytes")
    (formal_dir / "program_execution_manifest.json").write_text('{"status":"success"}\n', encoding="utf-8")

    original_file_digest = review_runtime_state._file_digest
    digest_calls: list[str] = []

    def counting_file_digest(path: Path) -> str:
        digest_calls.append(path.name)
        return original_file_digest(path)

    monkeypatch.setattr(review_runtime_state, "_file_digest", counting_file_digest)

    first = review_runtime_state.compute_author_materialization_digest(
        artifact_root=formal_dir,
        required_outputs=("factor_panel.parquet",),
        required_provenance_paths=("program_execution_manifest.json",),
    )
    assert sorted(digest_calls) == ["factor_panel.parquet", "program_execution_manifest.json"]

    digest_calls.clear()
    second = review_runtime_state.compute_author_materialization_digest(
        artifact_root=formal_dir,
        required_outputs=("factor_panel.parquet",),
        required_provenance_paths=("program_execution_manifest.json",),
    )

    assert second == first
    assert digest_calls == []
    assert (stage_dir / "review" / "state" / "materialization_digest_ledger.yaml").exists()


def test_compute_author_materialization_digest_fresh_bypasses_corrupt_cache(
    tmp_path: Path,
) -> None:
    stage_dir = tmp_path / "01_mandate"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "research_route.yaml").write_text("route: first\n", encoding="utf-8")
    (formal_dir / "program_execution_manifest.json").write_text("{}\n", encoding="utf-8")

    cached = review_runtime_state.compute_author_materialization_digest(
        artifact_root=formal_dir,
        required_outputs=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
    )
    ledger_path = stage_dir / "review" / "state" / "materialization_digest_ledger.yaml"
    ledger_text = ledger_path.read_text(encoding="utf-8")
    ledger_path.write_text(ledger_text.replace(cached, "0" * 64), encoding="utf-8")

    fresh = review_runtime_state.compute_author_materialization_digest_fresh(
        artifact_root=formal_dir,
        required_outputs=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
    )

    assert fresh == cached
    assert "0" * 64 in ledger_path.read_text(encoding="utf-8")
