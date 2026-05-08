from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_test_evidence_runtime import build_csf_test_evidence_from_train_freeze, scaffold_csf_test_evidence
from tests.runtime.test_csf_test_evidence_runtime import (
    _csf_test_evidence_draft,
    _prepare_csf_rank_ic_inputs,
    _prepare_csf_train_stage,
    _write_yaml,
)


def _prepare_valid_csf_test_evidence(lineage_root: Path) -> Path:
    _prepare_csf_train_stage(lineage_root)
    _prepare_csf_rank_ic_inputs(lineage_root)
    stage_dir = scaffold_csf_test_evidence(lineage_root)
    _write_yaml(stage_dir / "author" / "draft" / "csf_test_evidence_draft.yaml", _csf_test_evidence_draft(confirmed=True))
    build_csf_test_evidence_from_train_freeze(lineage_root)
    return stage_dir


def test_csf_test_evidence_scaffold_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_train_stage(lineage_root)

    stage_dir = scaffold_csf_test_evidence(lineage_root)

    draft = yaml.safe_load(
        (stage_dir / "author" / "draft" / "csf_test_evidence_draft.yaml").read_text(encoding="utf-8")
    )
    assert set(draft["groups"]) == {
        "window_contract",
        "variant_contract",
        "evidence_contract",
        "audit_contract",
        "delivery_contract",
    }
    assert set(draft["groups"]["variant_contract"]["draft"]) == {
        "selected_variant_ids",
        "selection_rule",
        "multiple_testing_note",
    }


def test_csf_test_evidence_build_shape_matches_contract(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_test_evidence(lineage_root)
    formal_dir = stage_dir / "author" / "formal"

    result = validate_stage_artifacts(formal_dir, load_artifact_contract("csf_test_evidence"))

    assert result.valid is True
    assert result.errors == []


def test_csf_test_evidence_summary_key_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_test_evidence(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    payload = yaml.safe_load((formal_dir / "rank_ic_summary.json").read_text(encoding="utf-8"))

    assert set(payload) == {
        "stage",
        "lineage_id",
        "factor_role",
        "selected_variant_ids",
        "primary_evidence_contract",
        "mean_rank_ic",
        "median_rank_ic",
        "num_dates",
    }
    assert payload["selected_variant_ids"] == ["baseline_v1"]


def test_csf_test_evidence_rank_ic_timeseries_columns_are_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    stage_dir = _prepare_valid_csf_test_evidence(lineage_root)
    formal_dir = stage_dir / "author" / "formal"

    table = pq.read_table(formal_dir / "rank_ic_timeseries.parquet")

    assert set(table.column_names) == {"date", "variant_id", "rank_ic"}
    assert table.to_pylist() == [{"date": "2024-07-01", "variant_id": "baseline_v1", "rank_ic": 1.0}]
