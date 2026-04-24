from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/artifacts/csf_data_ready_artifacts.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def _artifact(contract: dict, artifact_name: str) -> dict:
    return contract["artifacts"][artifact_name]


def _field_paths(artifact: dict) -> set[str]:
    return {field["path"] for field in artifact.get("fields", [])}


def test_csf_data_ready_artifact_contract_exists_and_declares_stage_shape() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["stage"] == "csf_data_ready"
    assert contract["stage_dir"] == "02_csf_data_ready/author/formal"
    assert contract["schema_id"] == "csf-data-ready-artifacts-v1"
    assert contract["schema_version"] == "v1"
    assert contract["unknown_machine_top_level_fields"] == "forbid"

    assert set(contract["artifacts"]) == {
        "panel_manifest.json",
        "asset_universe_membership.parquet",
        "cross_section_coverage.parquet",
        "eligibility_base_mask.parquet",
        "shared_feature_base",
        "asset_taxonomy_snapshot.parquet",
        "csf_data_contract.md",
        "csf_data_ready_gate_decision.md",
        "run_manifest.json",
        "rebuild_csf_data_ready.py",
        "artifact_catalog.md",
        "field_dictionary.md",
    }


def test_csf_data_ready_contract_locks_panel_manifest_fields() -> None:
    contract = _load_contract()
    panel_manifest = _artifact(contract, "panel_manifest.json")

    assert panel_manifest["type"] == "json"
    assert panel_manifest["unknown_top_level_fields"] == "forbid"
    assert _field_paths(panel_manifest) == {
        "stage",
        "lineage_id",
        "panel_primary_key",
        "cross_section_time_key",
        "asset_key",
        "shared_feature_outputs",
        "machine_artifacts",
        "coverage_floor_min_ratio",
    }

    stage_field = next(field for field in panel_manifest["fields"] if field["path"] == "stage")
    assert stage_field["type"] == "enum"
    assert stage_field["values"] == ["csf_data_ready"]

    coverage_floor = next(field for field in panel_manifest["fields"] if field["path"] == "coverage_floor_min_ratio")
    assert coverage_floor["type"] == "number"


def test_csf_data_ready_contract_locks_run_manifest_fields() -> None:
    contract = _load_contract()
    run_manifest = _artifact(contract, "run_manifest.json")

    assert run_manifest["type"] == "json"
    assert run_manifest["unknown_top_level_fields"] == "forbid"
    assert _field_paths(run_manifest) == {
        "stage",
        "lineage_id",
        "source_stage",
        "panel_primary_key",
        "cross_section_time_key",
        "asset_key",
        "universe_membership_rule",
        "group_taxonomy_reference",
        "eligibility_base_rule",
        "coverage_floor_rule",
        "shared_feature_outputs",
        "machine_artifacts",
        "consumer_stage",
        "frozen_inputs_note",
        "runtime_root_hint",
        "runtime_module",
        "runtime_function",
        "source_git_revision",
        "program_artifacts",
        "replay_working_directory",
        "replay_command",
    }


def test_csf_data_ready_contract_locks_parquet_columns() -> None:
    contract = _load_contract()

    assert _artifact(contract, "asset_universe_membership.parquet")["type"] == "parquet"
    assert _artifact(contract, "asset_universe_membership.parquet")["required_columns"] == [
        "date",
        "asset",
        "in_universe",
    ]
    assert _artifact(contract, "eligibility_base_mask.parquet")["required_columns"] == [
        "date",
        "asset",
        "eligible",
    ]
    assert _artifact(contract, "cross_section_coverage.parquet")["required_columns"] == [
        "date",
        "coverage_ratio",
        "asset_count",
    ]
    assert _artifact(contract, "asset_taxonomy_snapshot.parquet")["required_columns"] == [
        "asset",
        "date",
        "group_taxonomy_reference",
        "group_bucket",
    ]
    assert _artifact(contract, "shared_feature_base")["type"] == "directory"
    assert _artifact(contract, "shared_feature_base")["required_files"] == [
        {
            "path": "returns_panel.parquet",
            "type": "parquet",
            "required_columns": ["date", "asset", "return_1d"],
            "non_empty": True,
        },
        {
            "path": "liquidity_panel.parquet",
            "type": "parquet",
            "required_columns": ["date", "asset", "dollar_volume"],
            "non_empty": True,
        },
        {
            "path": "beta_inputs.parquet",
            "type": "parquet",
            "required_columns": ["date", "asset", "beta_proxy"],
            "non_empty": True,
        },
    ]


def test_csf_data_ready_contract_field_paths_are_unique() -> None:
    contract = _load_contract()

    for artifact_name, artifact in contract["artifacts"].items():
        paths = [field["path"] for field in artifact.get("fields", [])]
        assert len(paths) == len(set(paths)), artifact_name
