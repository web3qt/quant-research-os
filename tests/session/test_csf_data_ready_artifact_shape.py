from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_data_ready_runtime import build_csf_data_ready_from_mandate
from tests.runtime.test_csf_data_ready_runtime import (
    _csf_data_ready_draft,
    _prepare_mandate_stage,
    _write_yaml,
)


def _build_valid_csf_data_ready(lineage_root: Path) -> Path:
    _prepare_mandate_stage(lineage_root)
    stage_dir = lineage_root / "02_csf_data_ready"
    stage_dir.mkdir(parents=True)
    _write_yaml(stage_dir / "author" / "draft" / "csf_data_ready_freeze_draft.yaml", _csf_data_ready_draft(confirmed=True))
    build_csf_data_ready_from_mandate(lineage_root)
    return stage_dir / "author" / "formal"


def _field_paths(artifact: dict) -> set[str]:
    return {field["path"] for field in artifact.get("fields", [])}


def test_generated_csf_data_ready_file_tree_matches_artifact_contract(tmp_path: Path) -> None:
    formal_dir = _build_valid_csf_data_ready(tmp_path / "outputs" / "csf_case")
    contract = load_artifact_contract("csf_data_ready")

    assert set(item.name for item in formal_dir.iterdir()) == set(contract["artifacts"])
    assert set(item.name for item in (formal_dir / "shared_feature_base").iterdir()) == {
        "returns_panel.parquet",
        "liquidity_panel.parquet",
        "beta_inputs.parquet",
    }


def test_generated_csf_data_ready_json_shapes_match_contract(tmp_path: Path) -> None:
    formal_dir = _build_valid_csf_data_ready(tmp_path / "outputs" / "csf_case")
    contract = load_artifact_contract("csf_data_ready")

    for artifact_name in ("panel_manifest.json", "run_manifest.json"):
        payload = yaml.safe_load((formal_dir / artifact_name).read_text(encoding="utf-8"))
        assert set(payload) == _field_paths(contract["artifacts"][artifact_name])


def test_generated_csf_data_ready_split_sample_report_matches_contract(tmp_path: Path) -> None:
    formal_dir = _build_valid_csf_data_ready(tmp_path / "outputs" / "csf_case")
    contract = load_artifact_contract("csf_data_ready")
    payload = yaml.safe_load((formal_dir / "split_sample_adequacy_report.yaml").read_text(encoding="utf-8"))

    assert set(payload) == _field_paths(contract["artifacts"]["split_sample_adequacy_report.yaml"])
    assert payload["sample_unit"] == "cross_section_snapshot"
    assert payload["final_verdict"] == "PASS"
    assert payload["split_sample_counts"] == {
        "train": 1,
        "test": 1,
        "backtest": 1,
        "holdout": 1,
    }
    assert payload["minimum_required"] == {
        "train": 1,
        "test": 1,
        "backtest": 1,
        "holdout": 1,
    }
    assert payload["adequacy"] == {
        "train": "pass",
        "test": "pass",
        "backtest": "pass",
        "holdout": "pass",
    }


def test_generated_csf_data_ready_parquet_columns_match_contract(tmp_path: Path) -> None:
    formal_dir = _build_valid_csf_data_ready(tmp_path / "outputs" / "csf_case")
    contract = load_artifact_contract("csf_data_ready")

    for artifact_name in (
        "asset_universe_membership.parquet",
        "cross_section_coverage.parquet",
        "eligibility_base_mask.parquet",
        "asset_taxonomy_snapshot.parquet",
    ):
        table = pq.read_table(formal_dir / artifact_name)
        assert contract["artifacts"][artifact_name]["required_columns"] == table.schema.names

    for child in contract["artifacts"]["shared_feature_base"]["required_files"]:
        table = pq.read_table(formal_dir / "shared_feature_base" / child["path"])
        assert child["required_columns"] == table.schema.names


def test_generated_csf_data_ready_passes_artifact_shape_validator(tmp_path: Path) -> None:
    formal_dir = _build_valid_csf_data_ready(tmp_path / "outputs" / "csf_case")

    result = validate_stage_artifacts(formal_dir, load_artifact_contract("csf_data_ready"))

    assert result.valid is True
    assert result.errors == []
