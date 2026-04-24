from __future__ import annotations

from pathlib import Path

import yaml

from runtime.tools.artifact_contract_runtime import load_artifact_contract, validate_stage_artifacts
from runtime.tools.csf_signal_ready_runtime import (
    build_csf_signal_ready_from_data_ready,
    scaffold_csf_signal_ready,
)
from tests.runtime.test_csf_signal_ready_runtime import _prepare_csf_data_ready_stage, _write_yaml


def _confirmed_csf_signal_ready_draft() -> dict:
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


def test_csf_signal_ready_scaffold_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_data_ready_stage(lineage_root)

    stage_dir = scaffold_csf_signal_ready(lineage_root)

    draft = yaml.safe_load(
        (stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml").read_text(encoding="utf-8")
    )
    assert set(draft["groups"]) == {
        "factor_identity",
        "panel_contract",
        "factor_expression",
        "context_contract",
        "delivery_contract",
    }
    assert draft["groups"]["panel_contract"]["draft"]["panel_primary_key"] == ["date", "asset"]
    assert draft["groups"]["panel_contract"]["draft"]["coverage_min_ratio"] == 1.0


def test_csf_signal_ready_build_shape_matches_contract(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_data_ready_stage(lineage_root)
    stage_dir = scaffold_csf_signal_ready(lineage_root)
    _write_yaml(
        stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml",
        _confirmed_csf_signal_ready_draft(),
    )

    build_csf_signal_ready_from_data_ready(lineage_root)
    formal_dir = stage_dir / "author" / "formal"

    result = validate_stage_artifacts(formal_dir, load_artifact_contract("csf_signal_ready"))

    assert result.valid is True
    assert result.errors == []


def test_csf_signal_ready_yaml_key_shape_is_stable(tmp_path: Path) -> None:
    lineage_root = tmp_path / "outputs" / "csf_case"
    _prepare_csf_data_ready_stage(lineage_root)
    stage_dir = scaffold_csf_signal_ready(lineage_root)
    _write_yaml(
        stage_dir / "author" / "draft" / "csf_signal_ready_freeze_draft.yaml",
        _confirmed_csf_signal_ready_draft(),
    )

    build_csf_signal_ready_from_data_ready(lineage_root)
    formal_dir = stage_dir / "author" / "formal"
    factor_manifest = yaml.safe_load((formal_dir / "factor_manifest.yaml").read_text(encoding="utf-8"))
    component_manifest = yaml.safe_load((formal_dir / "component_factor_manifest.yaml").read_text(encoding="utf-8"))

    assert set(factor_manifest) == {
        "stage",
        "lineage_id",
        "factor_id",
        "factor_version",
        "factor_direction",
        "factor_structure",
        "panel_primary_key",
        "raw_factor_fields",
        "derived_factor_fields",
        "final_score_field",
        "as_of_semantics",
        "coverage_min_ratio",
        "coverage_contract",
        "missing_value_policy",
        "input_field_map",
    }
    assert set(component_manifest) == {
        "stage",
        "lineage_id",
        "factor_structure",
        "component_factor_ids",
        "score_combination_formula",
        "combination_policy",
    }
