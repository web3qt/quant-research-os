from pathlib import Path

from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from runtime.tools.review_skillgen.review_scope_builder import build_review_scope
from runtime.tools.tss_test_evidence_runtime import build_tss_test_evidence_from_train_freeze
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.runtime.test_tss_test_evidence_runtime import (
    _prepare_tss_train_freeze_stage,
    _tss_test_evidence_draft,
    _write_yaml,
)


def _prepare_valid_tss_test_evidence_stage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "tss_case"
    _prepare_tss_train_freeze_stage(lineage_root)
    ensure_stage_program(lineage_root, "tss_test_evidence")
    write_fake_stage_provenance(lineage_root, "tss_test_evidence")
    stage_dir = lineage_root / "05_tss_test_evidence"
    _write_yaml(
        stage_dir / "author" / "draft" / "tss_test_evidence_freeze_draft.yaml",
        _tss_test_evidence_draft(confirmed=True),
    )
    build_tss_test_evidence_from_train_freeze(lineage_root)
    assert (stage_dir / "author" / "formal" / "program_execution_manifest.json").exists()
    return stage_dir


def _run_tss_test_evidence_preflight(stage_dir: Path) -> dict:
    return run_review_preflight(
        explicit_context={
            "stage": "tss_test_evidence",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(stage_dir / "author" / "formal"),
            "lineage_id": stage_dir.parent.name,
        }
    )


def test_review_preflight_passes_runtime_built_tss_test_evidence_outputs(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_tss_test_evidence_stage(tmp_path)

    payload = _run_tss_test_evidence_preflight(stage_dir)

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_blocks_tss_test_evidence_missing_split_threshold_attestation(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_tss_test_evidence_stage(tmp_path)
    (stage_dir / "author" / "formal" / "split_threshold_attestation.yaml").unlink()

    payload = _run_tss_test_evidence_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert (
        "ARTIFACT-CONTRACT-001: split_threshold_attestation.yaml: missing required artifact"
        in payload["content_findings"]
    )


def test_review_preflight_blocks_tss_test_evidence_variant_drift(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_tss_test_evidence_stage(tmp_path)
    (stage_dir / "author" / "formal" / "tss_selected_variants_test.csv").write_text(
        "variant_id,horizon,status\nleaked_variant,1d,selected\n",
        encoding="utf-8",
    )

    payload = _run_tss_test_evidence_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any("TSS-TEST-SEMANTIC-001" in item for item in payload["content_findings"])


def test_review_scope_marks_tss_test_evidence_proof_artifacts_as_upstream_binding() -> None:
    scope = build_review_scope(
        stage="tss_test_evidence",
        required_artifact_paths=[
            "event_forward_return.parquet",
            "signal_performance_summary.json",
            "tss_test_gate_table.csv",
            "tss_selected_variants_test.csv",
            "split_threshold_attestation.yaml",
            "selected_variant_membership_proof.csv",
            "upstream_binding_digest_ledger.yaml",
        ],
        required_provenance_paths=["program_execution_manifest.json"],
    )

    assert scope["upstream_binding_artifact_paths"] == [
        "selected_variant_membership_proof.csv",
        "split_threshold_attestation.yaml",
        "upstream_binding_digest_ledger.yaml",
    ]
