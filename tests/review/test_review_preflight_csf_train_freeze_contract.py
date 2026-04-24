from __future__ import annotations

from pathlib import Path

import yaml

from runtime.tools.review_skillgen.review_preflight import run_review_preflight
from tests.helpers.lineage_program_support import ensure_stage_program, write_fake_stage_provenance
from tests.runtime.test_csf_signal_ready_semantic_validation import _build_valid_formal_dir
from tests.runtime.test_csf_signal_ready_runtime import _write_yaml
from tests.runtime.test_csf_train_runtime import _csf_train_freeze_draft
from runtime.tools.csf_train_runtime import build_csf_train_freeze_from_signal_ready, scaffold_csf_train_freeze


def _valid_train_draft() -> dict:
    draft = _csf_train_freeze_draft(confirmed=True)
    search = draft["groups"]["search_governance_contract"]["draft"]
    search["candidate_variant_ids"] = ["baseline_v1", "beta_neutral_v1"]
    search["kept_variant_ids"] = ["baseline_v1"]
    search["rejected_variant_ids"] = ["beta_neutral_v1"]
    search["frozen_signal_contract_reference"] = "03_csf_signal_ready/author/formal/factor_contract.md"
    delivery = draft["groups"]["delivery_contract"]["draft"]
    delivery["machine_artifacts"] = [
        "csf_train_freeze.yaml",
        "train_factor_quality.parquet",
        "train_variant_ledger.csv",
        "train_variant_rejects.csv",
    ]
    delivery["consumer_stage"] = "csf_test_evidence"
    return draft


def _prepare_valid_csf_train_freeze_stage(tmp_path: Path) -> Path:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _build_valid_formal_dir(lineage_root)
    ensure_stage_program(lineage_root, "csf_train_freeze")
    write_fake_stage_provenance(lineage_root, "csf_train_freeze")
    stage_dir = scaffold_csf_train_freeze(lineage_root)
    _write_yaml(stage_dir / "author" / "draft" / "csf_train_freeze_draft.yaml", _valid_train_draft())
    build_csf_train_freeze_from_signal_ready(lineage_root)
    return stage_dir


def _run_csf_train_freeze_preflight(stage_dir: Path) -> dict:
    return run_review_preflight(
        explicit_context={
            "stage": "csf_train_freeze",
            "stage_dir": str(stage_dir),
            "lineage_root": str(stage_dir.parent),
            "author_formal_dir": str(stage_dir / "author" / "formal"),
            "lineage_id": stage_dir.parent.name,
        }
    )


def test_review_preflight_passes_runtime_built_csf_train_freeze_outputs(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_train_freeze_stage(tmp_path)

    payload = _run_csf_train_freeze_preflight(stage_dir)

    assert payload["status"] == "PASS"
    assert payload["content_findings"] == []
    assert payload["upstream_binding_findings"] == []


def test_review_preflight_blocks_csf_train_freeze_missing_contract_artifact(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_train_freeze_stage(tmp_path)
    (stage_dir / "author" / "formal" / "train_neutralization_diagnostics.parquet").unlink()

    payload = _run_csf_train_freeze_preflight(stage_dir)

    assert payload["status"] == "FAIL"
    assert any(
        item
        == "ARTIFACT-CONTRACT-001: train_neutralization_diagnostics.parquet: missing required artifact"
        for item in payload["content_findings"]
    )


def test_review_preflight_blocks_csf_train_freeze_governable_axis_overlap(tmp_path: Path) -> None:
    stage_dir = _prepare_valid_csf_train_freeze_stage(tmp_path)
    formal_dir = stage_dir / "author" / "formal"
    payload = yaml.safe_load((formal_dir / "csf_train_freeze.yaml").read_text(encoding="utf-8"))
    payload["search_governance_contract"]["train_governable_axes"].append("raw_factor_fields")
    _write_yaml(formal_dir / "csf_train_freeze.yaml", payload)

    result = _run_csf_train_freeze_preflight(stage_dir)

    assert result["status"] == "FAIL"
    assert any("CSF-TRAIN-SEMANTIC-001" in item for item in result["content_findings"])
    assert any("CSF-TRAIN-BIND-003" in item for item in result["upstream_binding_findings"])
