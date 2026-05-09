from __future__ import annotations

from pathlib import Path

import pytest

from runtime.tools.lineage_lock_ledger import (
    FROZEN_ARTIFACT_MUTATED,
    FrozenArtifactMutationError,
    assert_lineage_locks_intact,
    lock_reviewed_stage,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _prepare_locked_stage(lineage_root: Path) -> Path:
    stage_dir = lineage_root / "01_mandate"
    _write(stage_dir / "author" / "formal" / "research_route.yaml", "research_route: cross_sectional_factor\n")
    _write(stage_dir / "author" / "formal" / "program_execution_manifest.json", "{}\n")
    _write(stage_dir / "review" / "closure" / "stage_gate_review.yaml", "final_verdict: PASS\n")
    _write(stage_dir / "review" / "closure" / "stage_completion_certificate.yaml", "final_verdict: PASS\n")
    _write(stage_dir / "review" / "closure" / "latest_review_pack.yaml", "final_verdict: PASS\n")
    return stage_dir


def test_lock_reviewed_stage_writes_author_and_closure_files(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = _prepare_locked_stage(lineage_root)

    payload = lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        locked_at="2026-05-09T00:00:00+00:00",
    )

    assert payload["ledger_version"] == 1
    assert payload["lineage_id"] == "btc_alt"
    assert payload["locked_stages"]["mandate"]["locked_at_review_cycle_id"] == "cycle-1"
    files = payload["locked_stages"]["mandate"]["files"]
    assert [item["path"] for item in files] == [
        "01_mandate/author/formal/program_execution_manifest.json",
        "01_mandate/author/formal/research_route.yaml",
        "01_mandate/review/closure/latest_review_pack.yaml",
        "01_mandate/review/closure/stage_completion_certificate.yaml",
        "01_mandate/review/closure/stage_gate_review.yaml",
    ]
    assert {item["artifact_role"] for item in files} == {"author_formal", "review_closure"}


def test_lock_reviewed_stage_is_idempotent_when_digests_match(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = _prepare_locked_stage(lineage_root)

    first = lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        locked_at="2026-05-09T00:00:00+00:00",
    )
    second = lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
        locked_at="2026-05-09T01:00:00+00:00",
    )

    assert second == first


def test_lock_reviewed_stage_skips_non_pass_like_verdict(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = _prepare_locked_stage(lineage_root)

    payload = lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="NO-GO",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
    )

    assert payload["locked_stages"] == {}
    assert not (lineage_root / "lineage_lock_ledger.yaml").exists()


def test_assert_lineage_locks_intact_rejects_changed_locked_file(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = _prepare_locked_stage(lineage_root)
    lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
    )
    _write(stage_dir / "author" / "formal" / "research_route.yaml", "changed\n")

    with pytest.raises(FrozenArtifactMutationError) as exc_info:
        assert_lineage_locks_intact(lineage_root)

    assert exc_info.value.reason_code == FROZEN_ARTIFACT_MUTATED
    assert exc_info.value.path == "01_mandate/author/formal/research_route.yaml"
    assert exc_info.value.locked_stage == "mandate"
    assert exc_info.value.expected_sha256 != exc_info.value.observed_sha256
    assert "Restore 01_mandate/author/formal/research_route.yaml" in exc_info.value.next_action


def test_assert_lineage_locks_intact_rejects_removed_locked_file(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "btc_alt"
    stage_dir = _prepare_locked_stage(lineage_root)
    lock_reviewed_stage(
        lineage_root=lineage_root,
        stage_dir=stage_dir,
        stage="mandate",
        review_cycle_id="cycle-1",
        final_verdict="PASS",
        required_artifact_paths=["research_route.yaml"],
        required_provenance_paths=["program_execution_manifest.json"],
    )
    (stage_dir / "author" / "formal" / "research_route.yaml").unlink()

    with pytest.raises(FrozenArtifactMutationError) as exc_info:
        assert_lineage_locks_intact(lineage_root)

    assert exc_info.value.observed_sha256 is None
