from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/artifacts/csf_signal_ready_artifacts.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def _artifact(contract: dict, artifact_name: str) -> dict:
    return contract["artifacts"][artifact_name]


def _field_paths(artifact: dict) -> set[str]:
    return {field["path"] for field in artifact.get("fields", [])}


def test_csf_signal_ready_artifact_contract_exists_and_declares_stage_shape() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["stage"] == "csf_signal_ready"
    assert contract["stage_dir"] == "03_csf_signal_ready/author/formal"
    assert contract["schema_id"] == "csf-signal-ready-artifacts-v1"
    assert contract["schema_version"] == "v1"
    assert contract["unknown_machine_top_level_fields"] == "forbid"

    assert set(contract["artifacts"]) == {
        "factor_panel.parquet",
        "factor_manifest.yaml",
        "component_factor_manifest.yaml",
        "factor_coverage_report.parquet",
        "factor_group_context.parquet",
        "route_inheritance_contract.yaml",
        "factor_contract.md",
        "factor_field_dictionary.md",
        "csf_signal_ready_gate_decision.md",
        "run_manifest.json",
        "artifact_catalog.md",
        "field_dictionary.md",
    }


def test_csf_signal_ready_contract_locks_factor_manifest_fields() -> None:
    contract = _load_contract()
    factor_manifest = _artifact(contract, "factor_manifest.yaml")

    assert factor_manifest["type"] == "yaml"
    assert factor_manifest["unknown_top_level_fields"] == "forbid"
    assert _field_paths(factor_manifest) == {
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

    factor_direction = next(field for field in factor_manifest["fields"] if field["path"] == "factor_direction")
    assert factor_direction["type"] == "enum"
    assert factor_direction["values"] == ["high_better", "low_better"]

    factor_structure = next(field for field in factor_manifest["fields"] if field["path"] == "factor_structure")
    assert factor_structure["type"] == "enum"
    assert factor_structure["values"] == ["single_factor", "multi_factor_score"]

    coverage_min_ratio = next(field for field in factor_manifest["fields"] if field["path"] == "coverage_min_ratio")
    assert coverage_min_ratio["type"] == "number"


def test_csf_signal_ready_contract_locks_component_manifest_fields() -> None:
    contract = _load_contract()
    component_manifest = _artifact(contract, "component_factor_manifest.yaml")

    assert component_manifest["type"] == "yaml"
    assert component_manifest["unknown_top_level_fields"] == "forbid"
    assert _field_paths(component_manifest) == {
        "stage",
        "lineage_id",
        "factor_structure",
        "component_factor_ids",
        "score_combination_formula",
        "combination_policy",
    }


def test_csf_signal_ready_contract_locks_route_inheritance_fields() -> None:
    contract = _load_contract()
    route_contract = _artifact(contract, "route_inheritance_contract.yaml")

    assert route_contract["type"] == "yaml"
    assert route_contract["unknown_top_level_fields"] == "forbid"
    assert _field_paths(route_contract) == {
        "source_route_artifact",
        "source_route_digest_sha256",
        "research_route",
        "factor_role",
        "factor_structure",
        "portfolio_expression",
        "neutralization_policy",
        "target_strategy_reference",
        "group_taxonomy_reference",
        "target_strategy_reference_requirement_status",
        "group_taxonomy_reference_requirement_status",
        "inheritance_mode",
    }

    factor_role = next(field for field in route_contract["fields"] if field["path"] == "factor_role")
    assert factor_role["type"] == "enum"
    assert factor_role["values"] == ["standalone_alpha", "regime_filter", "combo_filter"]

    inheritance_mode = next(field for field in route_contract["fields"] if field["path"] == "inheritance_mode")
    assert inheritance_mode["type"] == "enum"
    assert inheritance_mode["values"] == ["exact_copy"]


def test_csf_signal_ready_contract_locks_run_manifest_fields() -> None:
    contract = _load_contract()
    run_manifest = _artifact(contract, "run_manifest.json")

    assert run_manifest["type"] == "json"
    assert run_manifest["unknown_top_level_fields"] == "forbid"
    assert _field_paths(run_manifest) == {
        "stage",
        "lineage_id",
        "source_stage",
        "research_route",
        "factor_role",
        "factor_structure",
        "portfolio_expression",
        "neutralization_policy",
        "program_dir",
        "program_entrypoint",
        "program_execution_manifest",
        "input_roots",
        "stage_outputs",
        "replay_command",
    }


def test_csf_signal_ready_contract_locks_parquet_static_columns() -> None:
    contract = _load_contract()

    assert _artifact(contract, "factor_panel.parquet")["type"] == "parquet"
    assert _artifact(contract, "factor_panel.parquet")["required_columns"] == ["date", "asset"]
    assert _artifact(contract, "factor_panel.parquet")["non_empty"] is True
    assert _artifact(contract, "factor_coverage_report.parquet")["required_columns"] == [
        "date",
        "coverage_ratio",
        "asset_count",
    ]
    assert _artifact(contract, "factor_coverage_report.parquet")["non_empty"] is True
    assert _artifact(contract, "factor_group_context.parquet")["required_columns"] == [
        "date",
        "asset",
        "group_context",
    ]
    assert _artifact(contract, "factor_group_context.parquet")["non_empty"] is True


def test_csf_signal_ready_contract_field_paths_are_unique() -> None:
    contract = _load_contract()

    for artifact_name, artifact in contract["artifacts"].items():
        paths = [field["path"] for field in artifact.get("fields", [])]
        assert len(paths) == len(set(paths)), artifact_name
