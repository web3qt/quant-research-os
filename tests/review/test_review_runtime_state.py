import json
from pathlib import Path

import pytest
import yaml

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ensure_adversarial_review_request,
    issue_reviewer_receipt,
)
from runtime.tools.review_skillgen.protected_state_guard import (
    REVIEWER_FINDINGS_UNBOUND,
    STALE_REVIEW_EVIDENCE,
    ProtectedStateError,
    assert_protected_review_state_intact,
)
from runtime.tools.review_skillgen import review_runtime_state
from runtime.tools.review_skillgen.review_runtime_state import (
    compute_author_materialization_digest,
    write_review_runtime_state,
)
from runtime.tools.review_skillgen.reviewer_write_scope_audit import write_reviewer_write_scope_baseline


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_artifact_digest_manifest(formal_dir: Path, *, artifacts: list[dict]) -> None:
    payload = {
        "schema_version": 1,
        "lineage_id": "digest-case",
        "stage_id": "tss_data_ready",
        "program_hash": "program-hash",
        "program_execution_manifest_path": "program_execution_manifest.json",
        "artifacts": artifacts,
    }
    (formal_dir / "artifact_digest_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _prepare_raw_findings_case(tmp_path: Path) -> tuple[Path, Path, list[str], list[str]]:
    lineage_root = tmp_path / "outputs" / "raw_binding_case"
    stage_dir = lineage_root / "01_mandate"
    required_outputs = ["mandate.md", "run_manifest.json"]
    required_provenance = ["program_execution_manifest.json"]
    for name in required_outputs:
        _write_text(stage_dir / "author" / "formal" / name, f"{name}: ok\n")
    _write_text(stage_dir / "author" / "formal" / "program_execution_manifest.json", "{}\n")
    request = ensure_adversarial_review_request(
        stage_dir,
        lineage_id=lineage_root.name,
        stage="mandate",
        author_identity="author-agent",
        author_session_id="author-session",
        required_program_dir="program/mandate",
        required_program_entrypoint="run_stage.py",
        required_artifact_paths=required_outputs,
        required_provenance_paths=required_provenance,
        program_hash="hash-1",
        stage_invoked_at="2026-05-12T00:00:00+00:00",
    )
    receipt = issue_reviewer_receipt(
        stage_dir,
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
        launcher_session_id="launcher-session",
        launcher_thread_id="launcher-thread",
        reviewer_agent_id="reviewer-child",
    )
    digest = compute_author_materialization_digest(
        artifact_root=stage_dir / "author" / "formal",
        required_outputs=required_outputs,
        required_provenance_paths=required_provenance,
    )
    write_review_runtime_state(
        stage_dir,
        review_state="review_in_progress",
        active_review_cycle_id=request["review_cycle_id"],
        review_requested_at=receipt["receipt_written_at"],
        review_bound_author_digest=digest,
        reviewer_identity="reviewer-agent",
        reviewer_session_id="review-session",
    )
    write_reviewer_write_scope_baseline(
        stage_dir,
        review_cycle_id=receipt["review_cycle_id"],
        launcher_thread_id=receipt["launcher_thread_id"],
        reviewer_agent_id=receipt["reviewer_agent_id"],
    )
    return lineage_root, stage_dir, required_outputs, required_provenance


def test_protected_guard_rejects_raw_findings_with_wrong_reviewer_agent(tmp_path: Path) -> None:
    lineage_root, stage_dir, required_outputs, required_provenance = _prepare_raw_findings_case(tmp_path)
    request = yaml.safe_load((stage_dir / "review/request/adversarial_review_request.yaml").read_text())
    _write_text(
        stage_dir / "review/result/reviewer_findings.raw.yaml",
        yaml.safe_dump(
            {
                "review_cycle_id": request["review_cycle_id"],
                "reviewer_agent_id": "launcher-main-thread",
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": [],
                "residual_risks": [],
            },
            sort_keys=False,
        ),
    )

    with pytest.raises(ProtectedStateError) as exc_info:
        assert_protected_review_state_intact(
            stage_dir=stage_dir,
            lineage_root=lineage_root,
            required_outputs=required_outputs,
            required_provenance_paths=required_provenance,
            allow_missing_state=False,
        )

    assert exc_info.value.reason_code == REVIEWER_FINDINGS_UNBOUND


def test_protected_guard_rejects_raw_findings_after_author_outputs_change(tmp_path: Path) -> None:
    lineage_root, stage_dir, required_outputs, required_provenance = _prepare_raw_findings_case(tmp_path)
    request = yaml.safe_load((stage_dir / "review/request/adversarial_review_request.yaml").read_text())
    receipt = yaml.safe_load((stage_dir / "review/request/reviewer_receipt.yaml").read_text())
    _write_text(
        stage_dir / "review/result/reviewer_findings.raw.yaml",
        yaml.safe_dump(
            {
                "review_cycle_id": request["review_cycle_id"],
                "reviewer_agent_id": receipt["reviewer_agent_id"],
                "review_loop_outcome": "CLOSURE_READY_PASS",
                "blocking_findings": [],
                "reservation_findings": [],
                "info_findings": [],
                "residual_risks": [],
            },
            sort_keys=False,
        ),
    )
    _write_text(stage_dir / "author" / "formal" / "mandate.md", "changed after reviewer receipt\n")

    with pytest.raises(ProtectedStateError) as exc_info:
        assert_protected_review_state_intact(
            stage_dir=stage_dir,
            lineage_root=lineage_root,
            required_outputs=required_outputs,
            required_provenance_paths=required_provenance,
            allow_missing_state=False,
        )

    assert exc_info.value.reason_code == STALE_REVIEW_EVIDENCE


def test_compute_author_materialization_digest_reuses_unchanged_file_digest_cache(
    tmp_path: Path,
    monkeypatch,
) -> None:
    stage_dir = tmp_path / "03_csf_signal_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "factor_manifest.yaml").write_text("factor: ok\n", encoding="utf-8")
    (formal_dir / "program_execution_manifest.json").write_text('{"status":"success"}\n', encoding="utf-8")

    original_file_digest = review_runtime_state._file_digest
    digest_calls: list[str] = []

    def counting_file_digest(path: Path) -> str:
        digest_calls.append(path.name)
        return original_file_digest(path)

    monkeypatch.setattr(review_runtime_state, "_file_digest", counting_file_digest)

    first = review_runtime_state.compute_author_materialization_digest(
        artifact_root=formal_dir,
        required_outputs=("factor_manifest.yaml",),
        required_provenance_paths=("program_execution_manifest.json",),
    )
    assert sorted(digest_calls) == ["factor_manifest.yaml", "program_execution_manifest.json"]

    digest_calls.clear()
    second = review_runtime_state.compute_author_materialization_digest(
        artifact_root=formal_dir,
        required_outputs=("factor_manifest.yaml",),
        required_provenance_paths=("program_execution_manifest.json",),
    )

    assert second == first
    assert digest_calls == []
    assert (stage_dir / "review" / "state" / "materialization_digest_ledger.yaml").exists()


def test_compute_author_materialization_digest_cached_path_is_order_insensitive(tmp_path: Path) -> None:
    stage_dir = tmp_path / "02_csf_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in ("panel_manifest.json", "run_manifest.json", "program_execution_manifest.json"):
        (formal_dir / name).write_text(f"{name}: ok\n", encoding="utf-8")

    first = review_runtime_state.compute_author_materialization_digest(
        artifact_root=formal_dir,
        required_outputs=["panel_manifest.json", "run_manifest.json"],
        required_provenance_paths=["program_execution_manifest.json"],
    )
    second = review_runtime_state.compute_author_materialization_digest(
        artifact_root=formal_dir,
        required_outputs=["run_manifest.json", "panel_manifest.json"],
        required_provenance_paths=["program_execution_manifest.json"],
    )

    assert second == first
    assert (stage_dir / "review" / "state" / "materialization_digest_ledger.yaml").exists()


def test_author_materialization_digest_rejects_parquet_without_digest_manifest(tmp_path: Path, monkeypatch) -> None:
    stage_dir = tmp_path / "02_tss_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "asset_time_index.parquet").write_bytes(b"parquet-bytes")
    (formal_dir / "program_execution_manifest.json").write_text("{}\n", encoding="utf-8")

    def reject_file_digest(path: Path) -> str:
        if path.name == "asset_time_index.parquet":
            raise AssertionError("parquet must not be content-hashed in runtime hot paths")
        return "small-file-digest"

    monkeypatch.setattr(review_runtime_state, "_file_digest", reject_file_digest)

    with pytest.raises(ValueError, match="ARTIFACT_DIGEST_MANIFEST_MISSING"):
        review_runtime_state.compute_author_materialization_digest_fresh(
            artifact_root=formal_dir,
            required_outputs=["asset_time_index.parquet"],
            required_provenance_paths=["program_execution_manifest.json"],
        )


def test_author_materialization_digest_uses_manifest_for_parquet_without_reading_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    stage_dir = tmp_path / "02_tss_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    parquet_path = formal_dir / "asset_time_index.parquet"
    parquet_path.write_bytes(b"parquet-bytes")
    (formal_dir / "program_execution_manifest.json").write_text("{}\n", encoding="utf-8")
    _write_artifact_digest_manifest(
        formal_dir,
        artifacts=[
            {
                "path": "asset_time_index.parquet",
                "size_bytes": parquet_path.stat().st_size,
                "digest_algorithm": "sha256",
                "sha256": "a" * 64,
                "artifact_kind": "machine",
                "generated_at": "2026-05-28T00:00:00+00:00",
            }
        ],
    )
    digest_calls: list[str] = []

    def counting_file_digest(path: Path) -> str:
        digest_calls.append(path.name)
        if path.name == "asset_time_index.parquet":
            raise AssertionError("parquet must not be content-hashed in runtime hot paths")
        return "small-file-digest"

    monkeypatch.setattr(review_runtime_state, "_file_digest", counting_file_digest)

    digest = review_runtime_state.compute_author_materialization_digest_fresh(
        artifact_root=formal_dir,
        required_outputs=["asset_time_index.parquet"],
        required_provenance_paths=["program_execution_manifest.json"],
    )

    assert isinstance(digest, str)
    assert len(digest) == 64
    assert digest_calls == ["program_execution_manifest.json"]


def test_author_materialization_digest_rejects_large_non_data_file_without_manifest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    stage_dir = tmp_path / "03_signal_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "large_report.txt").write_bytes(b"x" * 20)
    (formal_dir / "program_execution_manifest.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(review_runtime_state, "LARGE_ARTIFACT_CONTENT_DIGEST_LIMIT_BYTES", 8)

    with pytest.raises(ValueError, match="ARTIFACT_DIGEST_MANIFEST_MISSING"):
        review_runtime_state.compute_author_materialization_digest_fresh(
            artifact_root=formal_dir,
            required_outputs=["large_report.txt"],
            required_provenance_paths=["program_execution_manifest.json"],
        )


def test_author_materialization_digest_rejects_manifest_missing_required_data_artifact(tmp_path: Path) -> None:
    stage_dir = tmp_path / "02_tss_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    (formal_dir / "asset_time_index.parquet").write_bytes(b"parquet-bytes")
    (formal_dir / "program_execution_manifest.json").write_text("{}\n", encoding="utf-8")
    _write_artifact_digest_manifest(formal_dir, artifacts=[])

    with pytest.raises(ValueError, match="ARTIFACT_DIGEST_MANIFEST_INCOMPLETE"):
        review_runtime_state.compute_author_materialization_digest_fresh(
            artifact_root=formal_dir,
            required_outputs=["asset_time_index.parquet"],
            required_provenance_paths=["program_execution_manifest.json"],
        )


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


def test_author_materialization_digest_is_order_insensitive(tmp_path: Path) -> None:
    stage_dir = tmp_path / "02_csf_data_ready"
    formal_dir = stage_dir / "author" / "formal"
    formal_dir.mkdir(parents=True)
    for name in ("panel_manifest.json", "run_manifest.json", "program_execution_manifest.json"):
        (formal_dir / name).write_text(f"{name}: ok\n", encoding="utf-8")

    first = review_runtime_state.compute_author_materialization_digest_fresh(
        artifact_root=formal_dir,
        required_outputs=["panel_manifest.json", "run_manifest.json"],
        required_provenance_paths=["program_execution_manifest.json"],
    )
    second = review_runtime_state.compute_author_materialization_digest_fresh(
        artifact_root=formal_dir,
        required_outputs=["run_manifest.json", "panel_manifest.json"],
        required_provenance_paths=["program_execution_manifest.json"],
    )

    assert second == first
