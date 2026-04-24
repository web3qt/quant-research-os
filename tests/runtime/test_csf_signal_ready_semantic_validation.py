from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from runtime.tools.csf_signal_ready_contract_runtime import validate_csf_signal_ready_semantics
from runtime.tools.csf_signal_ready_runtime import build_csf_signal_ready_from_data_ready, scaffold_csf_signal_ready
from tests.runtime.test_csf_signal_ready_runtime import _prepare_csf_data_ready_stage, _write_yaml


def _valid_draft() -> dict:
    return {
        "groups": {
            "factor_identity": {
                "confirmed": True,
                "draft": {
                    "factor_id": "btc_lead_alt_follow",
                    "factor_version": "v1",
                    "factor_direction": "high_better",
                    "factor_structure": "single_factor",
                },
                "missing_items": [],
            },
            "panel_contract": {
                "confirmed": True,
                "draft": {
                    "panel_primary_key": ["date", "asset"],
                    "as_of_semantics": "Factor values are frozen at the cross-section close.",
                    "coverage_min_ratio": 1.0,
                    "coverage_contract": "Require complete fixture coverage per cross-section.",
                },
                "missing_items": [],
            },
            "factor_expression": {
                "confirmed": True,
                "draft": {
                    "raw_factor_fields": ["return_1d", "dollar_volume", "beta_proxy"],
                    "derived_factor_fields": ["lead_follow_score"],
                    "final_score_field": "factor_value",
                    "missing_value_policy": "Preserve nulls and report eligibility separately.",
                },
                "missing_items": [],
            },
            "context_contract": {
                "confirmed": True,
                "draft": {
                    "group_context_fields": ["sector_bucket"],
                    "component_factor_ids": [],
                    "score_combination_formula": "single_factor_passthrough",
                },
                "missing_items": [],
            },
            "delivery_contract": {
                "confirmed": True,
                "draft": {
                    "machine_artifacts": ["factor_panel.parquet", "factor_manifest.yaml"],
                    "consumer_stage": "csf_train_freeze",
                    "frozen_inputs_note": "Train may set preprocessing rules but not redefine the factor.",
                },
                "missing_items": [],
            },
        }
    }


def _build_valid_formal_dir(lineage_root: Path) -> Path:
    _prepare_csf_data_ready_stage(lineage_root)
    stage_dir = scaffold_csf_signal_ready(lineage_root)
    _write_yaml(stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml", _valid_draft())
    build_csf_signal_ready_from_data_ready(lineage_root)
    return stage_dir / "author" / "formal"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_parquet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    columns = {key: [row.get(key) for row in rows] for key in rows[0].keys()}
    pq.write_table(pa.table(columns), path)


def _write_empty_parquet(path: Path, schema: dict[str, pa.DataType]) -> None:
    pq.write_table(pa.table({key: pa.array([], type=value) for key, value in schema.items()}), path)


def test_csf_signal_semantics_accepts_runtime_built_outputs(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)

    result = validate_csf_signal_ready_semantics(formal_dir, lineage_root)

    assert result.valid is True
    assert result.errors == []


def test_csf_signal_semantics_rejects_missing_final_score_column(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    _write_parquet_rows(
        formal_dir / "factor_panel.parquet",
        [{"date": "2024-01-01", "asset": "SOLUSDT", "other_score": 1.0}],
    )

    result = validate_csf_signal_ready_semantics(formal_dir, lineage_root)

    assert "factor_panel.parquet: missing final_score_field column factor_value" in result.errors


def test_csf_signal_semantics_rejects_duplicate_factor_panel_key(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    _write_parquet_rows(
        formal_dir / "factor_panel.parquet",
        [
            {"date": "2024-01-01", "asset": "SOLUSDT", "factor_value": 1.0},
            {"date": "2024-01-01", "asset": "SOLUSDT", "factor_value": 2.0},
        ],
    )

    result = validate_csf_signal_ready_semantics(formal_dir, lineage_root)

    assert "factor_panel.parquet: duplicate key ('2024-01-01', 'SOLUSDT') for ['date', 'asset']" in result.errors


def test_csf_signal_semantics_rejects_non_numeric_final_score(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    _write_parquet_rows(
        formal_dir / "factor_panel.parquet",
        [{"date": "2024-01-01", "asset": "SOLUSDT", "factor_value": "high"}],
    )

    result = validate_csf_signal_ready_semantics(formal_dir, lineage_root)

    assert "factor_panel.parquet: final_score_field factor_value must be numeric or null" in result.errors


def test_csf_signal_semantics_rejects_unbound_raw_factor_field(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    manifest_path = formal_dir / "factor_manifest.yaml"
    manifest = _load_yaml(manifest_path)
    manifest["raw_factor_fields"].append("unbound_field")
    _write_yaml(manifest_path, manifest)

    result = validate_csf_signal_ready_semantics(formal_dir, lineage_root)

    assert "factor_manifest.yaml: raw_factor_fields missing input_field_map binding for unbound_field" in result.errors


def test_csf_signal_semantics_rejects_input_field_map_outside_csf_data_ready(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    manifest_path = formal_dir / "factor_manifest.yaml"
    manifest = _load_yaml(manifest_path)
    manifest["input_field_map"][0]["source_artifact"] = "../03_csf_signal_ready/secret.parquet"
    _write_yaml(manifest_path, manifest)

    result = validate_csf_signal_ready_semantics(formal_dir, lineage_root)

    assert "factor_manifest.yaml: input_field_map source_artifact must stay under csf_data_ready formal artifacts" in result.errors


def test_csf_signal_semantics_rejects_coverage_below_declared_min_ratio(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    _write_parquet_rows(
        formal_dir / "factor_coverage_report.parquet",
        [{"date": "2024-01-01", "coverage_ratio": 0.5, "asset_count": 1}],
    )

    result = validate_csf_signal_ready_semantics(formal_dir, lineage_root)

    assert "factor_coverage_report.parquet: min coverage_ratio 0.5 below coverage_min_ratio 1" in result.errors


def test_csf_signal_semantics_rejects_missing_group_context_when_group_neutral(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    _write_empty_parquet(
        formal_dir / "factor_group_context.parquet",
        {
            "date": pa.string(),
            "asset": pa.string(),
            "group_context": pa.string(),
        },
    )

    result = validate_csf_signal_ready_semantics(formal_dir, lineage_root)

    assert "factor_group_context.parquet: expected non-empty rows when group context is required" in result.errors


def test_csf_signal_semantics_rejects_train_learned_combination_formula(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    component_path = formal_dir / "component_factor_manifest.yaml"
    component_manifest = _load_yaml(component_path)
    component_manifest["score_combination_formula"] = "learned_weight_from_backtest"
    _write_yaml(component_path, component_manifest)

    result = validate_csf_signal_ready_semantics(formal_dir, lineage_root)

    assert "component_factor_manifest.yaml: score_combination_formula must be deterministic before train/test" in result.errors


def test_csf_signal_semantics_rejects_factor_structure_drift(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    formal_dir = _build_valid_formal_dir(lineage_root)
    component_path = formal_dir / "component_factor_manifest.yaml"
    component_manifest = _load_yaml(component_path)
    component_manifest["factor_structure"] = "multi_factor_score"
    _write_yaml(component_path, component_manifest)

    result = validate_csf_signal_ready_semantics(formal_dir, lineage_root)

    assert "factor_structure must match across factor_manifest.yaml, component_factor_manifest.yaml, route_inheritance_contract.yaml, and run_manifest.json" in result.errors
