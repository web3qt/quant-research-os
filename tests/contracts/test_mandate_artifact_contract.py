from __future__ import annotations

from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/artifacts/mandate_artifacts.yaml")


def _load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def _artifact(contract: dict, artifact_name: str) -> dict:
    return contract["artifacts"][artifact_name]


def _field_paths(artifact: dict) -> set[str]:
    return {field["path"] for field in artifact.get("fields", [])}


def test_mandate_artifact_contract_exists_and_declares_stage_shape() -> None:
    assert CONTRACT_PATH.exists()
    contract = _load_contract()

    assert contract["stage"] == "mandate"
    assert contract["stage_dir"] == "01_mandate/author/formal"
    assert contract["schema_id"] == "mandate-artifacts-v1"
    assert contract["schema_version"] == "v1"
    assert contract["unknown_machine_top_level_fields"] == "forbid"

    assert set(contract["artifacts"]) == {
        "mandate.md",
        "research_scope.md",
        "research_route.yaml",
        "time_split.json",
        "parameter_grid.yaml",
        "run_config.toml",
        "artifact_catalog.md",
        "field_dictionary.md",
    }


def test_mandate_contract_locks_research_route_shape_and_enums() -> None:
    contract = _load_contract()
    research_route = _artifact(contract, "research_route.yaml")
    paths = _field_paths(research_route)

    assert research_route["type"] == "yaml"
    assert research_route["unknown_top_level_fields"] == "forbid"
    assert {
        "research_route",
        "factor_role",
        "factor_structure",
        "portfolio_expression",
        "neutralization_policy",
        "target_strategy_reference",
        "group_taxonomy_reference",
        "excluded_routes",
        "route_rationale",
        "route_change_policy",
        "route_change_policy.before_downstream_freeze",
        "route_change_policy.after_downstream_freeze",
        "route_contract_version",
    }.issubset(paths)

    route_field = next(field for field in research_route["fields"] if field["path"] == "research_route")
    assert route_field["type"] == "enum"
    assert route_field["values"] == ["time_series_signal", "cross_sectional_factor"]

    role_field = next(field for field in research_route["fields"] if field["path"] == "factor_role")
    assert role_field["allowed_values_if_nonempty"] == ["standalone_alpha", "regime_filter", "combo_filter"]


def test_mandate_contract_locks_time_split_and_run_config_shape() -> None:
    contract = _load_contract()
    time_split = _artifact(contract, "time_split.json")
    run_config = _artifact(contract, "run_config.toml")

    assert time_split["type"] == "json"
    assert _field_paths(time_split) == {
        "train",
        "test",
        "backtest",
        "holdout",
        "bar_size",
        "holding_horizons",
        "policy_note",
    }

    assert run_config["type"] == "toml"
    assert _field_paths(run_config) == {
        "stage",
        "lineage_id",
        "market",
        "universe",
        "target_task",
        "data_source",
        "bar_size",
        "non_rust_exceptions",
    }

    stage_field = next(field for field in run_config["fields"] if field["path"] == "stage")
    assert stage_field["type"] == "enum"
    assert stage_field["values"] == ["mandate"]


def test_mandate_contract_locks_parameter_grid_shape() -> None:
    contract = _load_contract()
    parameter_grid = _artifact(contract, "parameter_grid.yaml")

    assert parameter_grid["type"] == "yaml"
    assert _field_paths(parameter_grid) == {"parameters", "note"}
    parameters_field = next(field for field in parameter_grid["fields"] if field["path"] == "parameters")
    assert parameters_field["type"] == "list[map]"


def test_mandate_contract_field_paths_are_unique() -> None:
    contract = _load_contract()

    for artifact_name, artifact in contract["artifacts"].items():
        paths = [field["path"] for field in artifact.get("fields", [])]
        assert len(paths) == len(set(paths)), artifact_name
